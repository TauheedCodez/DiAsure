from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models_db import User
from schemas_auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from auth_utils import hash_password, verify_password, create_access_token
from email_service import send_verification_email, send_password_reset_email
import uuid
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Token expiry configuration
VERIFICATION_TOKEN_EXPIRE_HOURS = 24
RESET_TOKEN_EXPIRE_HOURS = 1


# Additional Schemas
class MessageResponse(BaseModel):
    message: str


class VerifyEmailRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    new_password: str


# ==================== REGISTRATION ====================

@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user and send verification email.
    User cannot login until email is verified.
    """
    # Check if email already registered
    existing_user = db.query(User).filter(User.email == req.email).first()
    if existing_user:
        if existing_user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered. Please sign in."
            )
        else:
            # User registered but not verified - resend verification
            token = str(uuid.uuid4())
            existing_user.verification_token = token
            existing_user.verification_token_expires = datetime.utcnow() + timedelta(hours=VERIFICATION_TOKEN_EXPIRE_HOURS)
            db.commit()
            
            # Try to send email but don't block if it fails
            try:
                send_verification_email(existing_user.email, token, existing_user.name)
            except Exception as e:
                print(f"⚠️ Warning: Failed to send verification email: {e}")
                # Don't fail registration - user can request resend later
            
            return {"message": "Verification email resent. Please check your inbox."}
    
    # Create new user
    hashed_pw = hash_password(req.password)
    verification_token = str(uuid.uuid4())
    
    new_user = User(
        name=req.name,
        email=req.email,
        password_hash=hashed_pw,
        email_verified=False,
        verification_token=verification_token,
        verification_token_expires=datetime.utcnow() + timedelta(hours=VERIFICATION_TOKEN_EXPIRE_HOURS)
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Send verification email (non-blocking, don't fail if email fails)
    try:
        print(f"📧 Attempting to send verification email to {new_user.email}...")
        send_verification_email(new_user.email, verification_token, new_user.name)
        print(f"✅ Verification email sent successfully to {new_user.email}")
    except Exception as e:
        print(f"⚠️ Warning: Failed to send verification email: {e}")
        # Don't rollback user creation - they can request resend
        # Just log the error and continue
    
    return {"message": "Registration successful! Please check your email to verify your account."}


# ==================== EMAIL VERIFICATION ====================

@router.get("/verify-email/{token}")
def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Verify user email with token from email link.
    Returns access token for auto-login.
    """
    user = db.query(User).filter(User.verification_token == token).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification link"
        )
    
    # Check if token expired
    if user.verification_token_expires and datetime.utcnow() > user.verification_token_expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link has expired. Please request a new one."
        )
    
    # Verify user
    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()
    
    # Create access token for auto-login
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "message": "Email verified successfully!",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }


@router.post("/resend-verification", response_model=MessageResponse)
def resend_verification(req: VerifyEmailRequest, db: Session = Depends(get_db)):
    """
    Resend verification email to user.
    """
    user = db.query(User).filter(User.email == req.email).first()
    
    if not user:
        # Don't reveal if user exists (security)
        return {"message": "If the email is registered, a verification link has been sent."}
    
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified. Please sign in."
        )
    
    # Generate new token
    token = str(uuid.uuid4())
    user.verification_token = token
    user.verification_token_expires = datetime.utcnow() + timedelta(hours=VERIFICATION_TOKEN_EXPIRE_HOURS)
    db.commit()
    
    try:
        send_verification_email(user.email, token, user.name)
    except Exception as e:
        print(f"Error sending verification email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again."
        )
    
    return {"message": "Verification email sent. Please check your inbox."}


# ==================== LOGIN ====================

@router.post("/login", response_model=dict)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """
    Login user with email and password.
    User must have verified email.
    """
    user = db.query(User).filter(User.email == req.email).first()
    
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if email is verified
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before signing in. Check your inbox for the verification link."
        )
    
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }


# ==================== FORGOT PASSWORD ====================

@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(req: VerifyEmailRequest, db: Session = Depends(get_db)):
    """
    Request password reset email.
    Silent if email doesn't exist (security).
    """
    user = db.query(User).filter(User.email == req.email).first()
    
    if not user:
        # Don't reveal if user exists (security)
        return {"message": "If the email is registered, a password reset link has been sent."}
    
    # Only send reset to verified accounts
    if not user.email_verified:
        # Don't reveal that email is not verified
        return {"message": "If the email is registered, a password reset link has been sent."}
    
    # Generate reset token
    reset_token = str(uuid.uuid4())
    user.reset_token = reset_token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=RESET_TOKEN_EXPIRE_HOURS)
    db.commit()
    
    try:
        send_password_reset_email(user.email, reset_token, user.name)
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email. Please try again."
        )
    
    return {"message": "If the email is registered, a password reset link has been sent."}


# ==================== RESET PASSWORD ====================

@router.post("/reset-password/{token}", response_model=MessageResponse)
def reset_password(token: str, req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset password with token from email link.
    """
    user = db.query(User).filter(User.reset_token == token).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset link"
        )
    
    # Check if token expired
    if user.reset_token_expires and datetime.utcnow() > user.reset_token_expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset link has expired. Please request a new one."
        )
    
    # Update password
    user.password_hash = hash_password(req.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    
    return {"message": "Password reset successfully! You can now sign in with your new password."}


# ==================== GET CURRENT USER ====================

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth_utils import decode_access_token

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current user information.
    """
    return current_user
