import resend
import os
from datetime import datetime, timedelta

# Initialize Resend with API key
resend.api_key = os.getenv("RESEND_API_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


def send_verification_email(email: str, token: str, name: str):
    """Send email verification link to user"""
    
    verification_link = f"{FRONTEND_URL}/verify-email/{token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .container {{
                background: #ffffff;
                border-radius: 12px;
                padding: 40px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 32px;
                font-weight: 700;
                color: #0f766e;
                margin-bottom: 10px;
            }}
            .title {{
                font-size: 24px;
                font-weight: 600;
                color: #1f2937;
                margin-bottom: 20px;
            }}
            .content {{
                font-size: 16px;
                color: #4b5563;
                margin-bottom: 30px;
            }}
            .button {{
                display: inline-block;
                padding: 14px 32px;
                background: linear-gradient(135deg, #0f766e, #0891b2);
                color: #ffffff !important;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 16px;
                text-align: center;
            }}
            .button:hover {{
                background: linear-gradient(135deg, #0d6660, #0785a1);
            }}
            .link {{
                color: #0f766e;
                word-break: break-all;
                font-size: 14px;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #e5e7eb;
                text-align: center;
                font-size: 14px;
                color: #6b7280;
            }}
            .expiry {{
                margin-top: 20px;
                padding: 12px;
                background: #fef3c7;
                border-left: 4px solid #f59e0b;
                border-radius: 4px;
                font-size: 14px;
                color: #92400e;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">DiAsure</div>
            </div>
            
            <div class="title">Verify Your Email Address</div>
            
            <div class="content">
                <p>Hi {name},</p>
                <p>Welcome to DiAsure! To get started with your diabetic foot ulcer assessment account, please verify your email address by clicking the button below:</p>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verification_link}" class="button">Verify Email Address</a>
            </div>
            
            <div class="expiry">
                This verification link will expire in 24 hours.
            </div>
            
            <div class="footer">
                <p>If you didn't create an account with DiAsure, you can safely ignore this email.</p>
                <p style="margin-top: 10px;">© 2026 DiAsure. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        print(f"[Email Service] Sending verification email to {email}...")
        print(f"[Email Service] Using API key: {resend.api_key[:10]}... (truncated)")
        
        response = resend.Emails.send({
            "from": "DiAsure <onboarding@resend.dev>",
            "to": email,
            "subject": "Verify your DiAsure account",
            "html": html_content
        })
        
        print(f"[Email Service] Resend response: {response}")
        return response
    except Exception as e:
        print(f"[Email Service] ❌ Error sending verification email: {type(e).__name__}: {str(e)}")
        raise


def send_password_reset_email(email: str, token: str, name: str):
    """Send password reset link to user"""
    
    reset_link = f"{FRONTEND_URL}/reset-password/{token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .container {{
                background: #ffffff;
                border-radius: 12px;
                padding: 40px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 32px;
                font-weight: 700;
                color: #0f766e;
                margin-bottom: 10px;
            }}
            .title {{
                font-size: 24px;
                font-weight: 600;
                color: #1f2937;
                margin-bottom: 20px;
            }}
            .content {{
                font-size: 16px;
                color: #4b5563;
                margin-bottom: 30px;
            }}
            .button {{
                display: inline-block;
                padding: 14px 32px;
                background: linear-gradient(135deg, #0f766e, #0891b2);
                color: #ffffff !important;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 16px;
                text-align: center;
            }}
            .button:hover {{
                background: linear-gradient(135deg, #0d6660, #0785a1);
            }}
            .link {{
                color: #0f766e;
                word-break: break-all;
                font-size: 14px;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #e5e7eb;
                text-align: center;
                font-size: 14px;
                color: #6b7280;
            }}
            .expiry {{
                margin-top: 20px;
                padding: 12px;
                background: #fee2e2;
                border-left: 4px solid #ef4444;
                border-radius: 4px;
                font-size: 14px;
                color: #7f1d1d;
            }}
            .warning {{
                margin-top: 20px;
                padding: 12px;
                background: #fef3c7;
                border-radius: 4px;
                font-size: 14px;
                color: #92400e;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">DiAsure</div>
            </div>
            
            <div class="title">Reset Your Password</div>
            
            <div class="content">
                <p>Hi {name},</p>
                <p>We received a request to reset the password for your DiAsure account. Click the button below to create a new password:</p>
            </div>
            
            <div style="text-align: center; margin:30px 0;">
                <a href="{reset_link}" class="button">Reset Password</a>
            </div>
            
            <div class="expiry">
                This password reset link will expire in 1 hour.
            </div>
            
            <div class="warning">
                If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
            </div>
            
            <div class="footer">
                <p>For security reasons, we cannot tell you your current password.</p>
                <p style="margin-top: 10px;">© 2026 DiAsure. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        response = resend.Emails.send({
            "from": "DiAsure <onboarding@resend.dev>",
            "to": email,
            "subject": "Reset your DiAsure password",
            "html": html_content
        })
        return response
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        raise
