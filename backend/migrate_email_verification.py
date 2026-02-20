"""
Database migration script to add email verification and password reset columns.
Run this once to update the existing schema.
"""
from sqlalchemy import text
from database import engine

def migrate_add_email_verification():
    """Add email verification columns to users table"""
    
    with engine.connect() as conn:
        try:
            # Add email_verified column
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE NOT NULL
            """))
            
            # Add verification_token column
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS verification_token VARCHAR UNIQUE
            """))
            
            # Add verification_token_expires column
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS verification_token_expires TIMESTAMP
            """))
            
            # Add reset_token column
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS reset_token VARCHAR UNIQUE
            """))
            
            # Add reset_token_expires column
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP
            """))
            
            # Set existing users as verified (backward compatibility)
            conn.execute(text("""
                UPDATE users 
                SET email_verified = TRUE 
                WHERE email_verified IS NULL OR email_verified = FALSE
            """))
            
            conn.commit()
            print("✅ Migration completed successfully!")
            print("✅ All existing users have been marked as verified.")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Migration failed: {e}")
            raise


if __name__ == "__main__":
    print("Starting database migration...")
    migrate_add_email_verification()
