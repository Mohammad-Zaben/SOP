"""
User business logic layer
Handles user CRUD operations, status management, and user search functionality
"""
from typing import List, Optional, Dict, Any

from fastapi import HTTPException, status
from sqlmodel import Session, select

from ..core.security import get_password_hash
from ..models.user import User, UserStatus, UserRole
from ..schemas.user import UserCreate, UserUpdate
from ..utils.db_utils import check_unique_constraint, handle_database_errors
from ..utils.validation_utils import validate_enum_value


@handle_database_errors("user creation")
def create_user(session: Session, user_data: UserCreate) -> User:
    """
    Create a new user with hashed password and default settings.
    
    Args:
        session: Database session
        user_data: User creation data from UserCreate schema
        
    Returns:
        User: Created user instance
        
    Raises:
        HTTPException 400: If username or email already exists
        HTTPException 500: If unexpected error occurs during creation
    """
    # Check uniqueness constraints
    check_unique_constraint(
        session, User, "username", user_data.username, "Username already exists"
    )
    
    if user_data.email:
        check_unique_constraint(
            session, User, "email", user_data.email, "Email already exists"
        )
    
    # Hash the password before storing
    hashed_password = get_password_hash(user_data.password)
    
    # Create user instance with default role and status
    db_user = User(
        username=user_data.username,
        password=hashed_password,
        role=UserRole.USER,  # Default role
        email=user_data.email,
        phone=user_data.phone,
        shop_type=user_data.shop_type,
        location=user_data.location,
        status=UserStatus.ACTIVE  # Default status
    )
    
    # Add to session and commit
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    return db_user


def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
    """
    Retrieve a user by their ID.
    
    Args:
        session: Database session
        user_id: User ID to search for
        
    Returns:
        Optional[User]: User instance if found, None otherwise
    """
    statement = select(User).where(User.id == user_id)
    return session.exec(statement).first()


def update_user(session: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """
    Partially update user data (excluding password).
    
    Args:
        session: Database session
        user_id: ID of user to update
        user_update: Update data from UserUpdate schema
        
    Returns:
        Optional[User]: Updated user instance if found, None otherwise
    """
    # Get existing user
    user = get_user_by_id(session, user_id)
    if not user:
        return None
    
    # Update only provided fields
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    # Commit changes
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user


def change_user_status(session: Session, user_id: int, status: str) -> Optional[User]:
    """
    Update user status with validation.
    
    Args:
        session: Database session
        user_id: ID of user to update
        status: New status value (must be valid UserStatus enum value)
        
    Returns:
        Optional[User]: Updated user if found, None otherwise
        
    Raises:
        ValueError: If status is not a valid UserStatus value
    """
    # Validate status value using utility function
    valid_statuses = [s.value for s in UserStatus]
    validate_enum_value(status, valid_statuses, "status")
    
    # Get existing user
    user = get_user_by_id(session, user_id)
    if not user:
        return None
    
    # Update status
    user.status = UserStatus(status)
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user


def get_all_users(session: Session) -> List[User]:
    """
    Retrieve all users from the database.
    
    Args:
        session: Database session
        
    Returns:
        List[User]: List of all users (may be empty)
    """
    statement = select(User)
    return session.exec(statement).all()


def search_users(session: Session, filters: Dict[str, Any]) -> List[User]:
    """
    Search users based on provided filters.
    
    Args:
        session: Database session
        filters: Dictionary containing search criteria:
            - username: partial match (case-insensitive)
            - phone: exact match
            - location: partial match (case-insensitive)
            - shop_type: exact match
            - status: exact match
            
    Returns:
        List[User]: List of matching users (may be empty)
    """
    statement = select(User)
    
    # Apply filters dynamically
    if "username" in filters and filters["username"]:
        statement = statement.where(User.username.ilike(f"%{filters['username']}%"))
    
    if "phone" in filters and filters["phone"]:
        statement = statement.where(User.phone == filters["phone"])
    
    if "location" in filters and filters["location"]:
        statement = statement.where(User.location.ilike(f"%{filters['location']}%"))
    
    if "shop_type" in filters and filters["shop_type"]:
        statement = statement.where(User.shop_type == filters["shop_type"])
    
    if "status" in filters and filters["status"]:
        # Validate status before querying
        try:
            status_enum = UserStatus(filters["status"])
            statement = statement.where(User.status == status_enum)
        except ValueError:
            # Invalid status - return empty list
            return []
    
    return session.exec(statement).all()


def get_user_by_username(session: Session, username: str) -> Optional[User]:
    """
    Retrieve a user by their username (for authentication purposes).
    
    Args:
        session: Database session
        username: Username to search for
        
    Returns:
        Optional[User]: User instance if found, None otherwise
    """
    statement = select(User).where(User.username == username)
    return session.exec(statement).first()


def get_user_by_email(session: Session, email: str) -> Optional[User]:
    """
    Retrieve a user by their email address.
    
    Args:
        session: Database session
        email: Email address to search for
        
    Returns:
        Optional[User]: User instance if found, None otherwise
    """
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()
