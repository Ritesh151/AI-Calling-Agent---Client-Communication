#!/usr/bin/env python
"""
Grant admin access to a user by email.

Usage:
    python grant_admin.py ritesh.work.1510@gmail.com
    python grant_admin.py <email>
"""

import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.user import User


def grant_admin_access(email: str) -> bool:
    """Grant admin role to a user by email."""
    
    # Create database engine
    engine = create_engine(str(settings.DATABASE_URL))
    
    # Create session
    session = Session(engine)
    
    try:
        # Find user by email
        user = session.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ User not found: {email}")
            return False
        
        # Check current role
        print(f"📋 User: {user.username} ({user.email})")
        print(f"   Current role: {user.role}")
        
        # Update role to admin
        user.role = "admin"
        session.commit()
        
        print(f"✅ Admin access granted to {email}")
        print(f"   New role: {user.role}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python grant_admin.py <email>")
        print("Example: python grant_admin.py ritesh.work.1510@gmail.com")
        sys.exit(1)
    
    email = sys.argv[1]
    success = grant_admin_access(email)
    sys.exit(0 if success else 1)
