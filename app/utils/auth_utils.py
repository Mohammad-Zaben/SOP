"""
Authorization utilities for ownership validation and permission checks
Contains reusable functions for IDOR protection and role-based access control
"""
from typing import Optional, Union
from fastapi import HTTPException, status

from ..models.user import User, UserRole


def check_ownership_or_admin(
    current_user: User, 
    resource_user_id: int, 
    resource_name: str = "resource"
) -> None:
    """
    Check if current user owns the resource or is an admin.
    
    Args:
        current_user: Current authenticated user
        resource_user_id: User ID who owns the resource
        resource_name: Name of the resource for error message
        
    Raises:
        HTTPException 403: If user is not authorized to access this resource
    """
    if current_user.role != UserRole.ADMIN and current_user.id != resource_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized to access this {resource_name}"
        )


def check_admin_access(current_user: User, action: str = "perform this action") -> None:
    """
    Check if current user has admin privileges.
    
    Args:
        current_user: Current authenticated user
        action: Description of the action for error message
        
    Raises:
        HTTPException 403: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Admin access required to {action}"
        )


def check_resource_ownership(
    current_user: User,
    resource: Optional[object],
    resource_name: str = "resource",
    user_id_field: str = "user_id"
) -> object:
    """
    Check if a resource exists and if user has access to it.
    
    Args:
        current_user: Current authenticated user
        resource: The resource object to check (can be None)
        resource_name: Name of the resource for error messages
        user_id_field: Name of the field containing the owner's user ID
        
    Returns:
        object: The resource if access is authorized
        
    Raises:
        HTTPException 404: If resource not found
        HTTPException 403: If user is not authorized to access this resource
    """
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_name.capitalize()} not found"
        )
    
    # Get the user_id from the resource
    resource_user_id = getattr(resource, user_id_field, None)
    if resource_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resource ownership validation failed"
        )
    
    # Check ownership or admin access
    check_ownership_or_admin(current_user, resource_user_id, resource_name)
    
    return resource


def is_admin(user: User) -> bool:
    """
    Check if user has admin role.
    
    Args:
        user: User to check
        
    Returns:
        bool: True if user is admin, False otherwise
    """
    return user.role == UserRole.ADMIN


def is_owner_or_admin(user: User, resource_user_id: int) -> bool:
    """
    Check if user owns the resource or is an admin.
    
    Args:
        user: User to check
        resource_user_id: User ID who owns the resource
        
    Returns:
        bool: True if user is owner or admin, False otherwise
    """
    return user.role == UserRole.ADMIN or user.id == resource_user_id
