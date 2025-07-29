"""
Authentication dependencies for protected routes
Contains get_current_user, get_current_admin_user, and other reusable auth dependencies
"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select

from ..core.database import get_session
from ..core.security import decode_access_token
from ..models.user import User, UserRole, UserStatus

# HTTP Bearer token scheme for extracting JWT from Authorization header
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
) -> User:
    """
    Extract and validate JWT token, then return the current authenticated user.
    
    Args:
        credentials: JWT token from Authorization header
        session: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException 401: If token is invalid or user not found
    """
    # Decode the JWT token to get user information
    token_data = decode_access_token(credentials.credentials)
    
    # Extract user ID from token payload (typically stored in 'sub' claim)
    user_id: Optional[int] = token_data.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Query the database to get the current user
    statement = select(User).where(User.id == user_id)
    user = session.exec(statement).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def get_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensure the current user has an active status.
    
    Args:
        current_user: Current authenticated user from get_current_user
        
    Returns:
        User: Active user
        
    Raises:
        HTTPException 403: If user is suspended or banned
    """
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User account is {current_user.status.value}. Access denied."
        )
    
    return current_user


def get_current_admin(current_user: User = Depends(get_active_user)) -> User:
    """
    Ensure the current user has admin role and is active.
    
    Args:
        current_user: Current active user from get_active_user
        
    Returns:
        User: Admin user
        
    Raises:
        HTTPException 403: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


# Optional: Get current user but allow None (for optional authentication)
def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    session: Session = Depends(get_session)
) -> Optional[User]:
    """
    Extract current user if token is provided, otherwise return None.
    Useful for endpoints that work both authenticated and unauthenticated.
    
    Args:
        credentials: Optional JWT token from Authorization header
        session: Database session
        
    Returns:
        Optional[User]: Current user if authenticated, None otherwise
    """
    if credentials is None:
        return None
    
    try:
        # Decode the JWT token
        token_data = decode_access_token(credentials.credentials)
        user_id: Optional[int] = token_data.get("sub")
        
        if user_id is None:
            return None
        
        # Query the database to get the current user
        statement = select(User).where(User.id == user_id)
        user = session.exec(statement).first()
        
        return user
    except HTTPException:
        # If token is invalid, return None instead of raising error
        return None
