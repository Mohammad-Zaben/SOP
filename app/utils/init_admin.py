"""
Admin user initialization utility
Ensures an admin user exists during application startup
"""
import logging
from datetime import datetime
from sqlmodel import Session, select

from ..core.database import SessionLocal
from ..core.security import get_password_hash
from ..models.user import User, UserRole, UserStatus

logger = logging.getLogger(__name__)


def create_admin_user_if_not_exists() -> None:
    """
    Check if an admin user exists, and create one if it doesn't.
    
    Creates a default admin user with:
    - username: admin
    - password: admin123 (hashed)
    - role: admin
    - status: active
    - shop_type: general
    
    This function is designed to run once during application startup.
    """
    session = SessionLocal()
    try:
        # Check if admin user already exists
        statement = select(User).where(
            User.username == "admin", 
            User.role == UserRole.ADMIN
        )
        existing_admin = session.exec(statement).first()
        
        if existing_admin:
            logger.info("Admin user already exists, skipping creation")
            return
        
        # Create new admin user
        hashed_password = get_password_hash("admin123")
        admin_user = User(
            username="admin",
            password=hashed_password,
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            shop_type="general",
            created_at=datetime.utcnow()
        )
        
        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)
        
        logger.info(f"Default admin user created successfully with ID: {admin_user.id}")
        
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        session.rollback()
        raise
    finally:
        session.close()
