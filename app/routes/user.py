"""
User management API routes
Handles user profile operations, admin user management, and user-related endpoints
"""
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session

from ..core.database import get_session
from ..dependencies.auth import get_active_user, get_current_admin
from ..models.user import User
from ..schemas.user import UserCreate, UserRead, UserUpdate
from ..services import user_service


router = APIRouter()


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin)
) -> UserRead:
    """
    Create a new user (admin only).
    
    Args:
        user_data: User creation data from UserCreate schema
        session: Database session dependency
        admin_user: Current admin user from auth dependency
        
    Returns:
        UserRead: Created user data
        
    Raises:
        HTTPException 400: If username or email already exists
        HTTPException 403: If user is not admin
    """
    created_user = user_service.create_user(session, user_data)
    return UserRead.from_orm(created_user)


@router.get("/{user_id}", response_model=UserRead, status_code=status.HTTP_200_OK)
def get_user_by_id(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_active_user)
) -> UserRead:
    """
    Get user by ID (admin can access any user, regular users can only access themselves).
    
    Args:
        user_id: ID of the user to retrieve
        session: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        UserRead: User data
        
    Raises:
        HTTPException 403: If regular user tries to access another user
        HTTPException 404: If user not found
    """
    # IDOR protection: regular users can only access their own data
    from ..models.user import UserRole
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only access your own profile."
        )
    
    user = user_service.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserRead.from_orm(user)


@router.put("/{user_id}", response_model=UserRead, status_code=status.HTTP_200_OK)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_active_user)
) -> UserRead:
    """
    Update user data (admin can update any user, regular users can only update themselves).
    
    Args:
        user_id: ID of the user to update
        user_update: User update data from UserUpdate schema
        session: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        UserRead: Updated user data
        
    Raises:
        HTTPException 403: If regular user tries to update another user
        HTTPException 404: If user not found
    """
    # IDOR protection: regular users can only update their own data
    from ..models.user import UserRole
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only update your own profile."
        )
    
    updated_user = user_service.update_user(session, user_id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserRead.from_orm(updated_user)


@router.get("/", response_model=List[UserRead], status_code=status.HTTP_200_OK)
def list_users(
    username: Optional[str] = Query(None, description="Filter by username (partial match)"),
    phone: Optional[str] = Query(None, description="Filter by phone number"),
    location: Optional[str] = Query(None, description="Filter by location (partial match)"),
    shop_type: Optional[str] = Query(None, description="Filter by shop type"),
    user_status: Optional[str] = Query(None, alias="status", description="Filter by user status"),
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin)
) -> List[UserRead]:
    """
    List/search users with optional filters (admin only).
    
    Args:
        username: Optional username filter (partial match)
        phone: Optional phone filter (exact match)
        location: Optional location filter (partial match)
        shop_type: Optional shop type filter (exact match)
        user_status: Optional status filter (exact match)
        session: Database session dependency
        admin_user: Current admin user from auth dependency
        
    Returns:
        List[UserRead]: List of users matching the filters
        
    Raises:
        HTTPException 403: If user is not admin
    """
    # Build filters dictionary
    filters = {}
    if username is not None:
        filters["username"] = username
    if phone is not None:
        filters["phone"] = phone
    if location is not None:
        filters["location"] = location
    if shop_type is not None:
        filters["shop_type"] = shop_type
    if user_status is not None:
        filters["status"] = user_status
    
    # Get users based on filters
    if filters:
        users = user_service.search_users(session, filters)
    else:
        users = user_service.get_all_users(session)
    
    return [UserRead.from_orm(user) for user in users]
