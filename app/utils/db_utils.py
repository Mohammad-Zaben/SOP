"""
Database operation utilities and error handling
Contains reusable functions for database transactions and error management
"""
from typing import Callable, Any, Optional
from functools import wraps

from fastapi import HTTPException, status
from sqlmodel import Session


def handle_database_errors(operation_name: str = "database operation"):
    """
    Decorator to handle database errors with automatic rollback.
    
    Args:
        operation_name: Name of the operation for error message
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(session: Session, *args, **kwargs) -> Any:
            try:
                return func(session, *args, **kwargs)
            except HTTPException:
                # Re-raise HTTPExceptions (our custom validation errors)
                session.rollback()
                raise
            except Exception as e:
                # Handle any unexpected database or other errors
                session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"An unexpected error occurred during {operation_name}."
                )
        return wrapper
    return decorator


def safe_commit(session: Session, entity: Any) -> Any:
    """
    Safely commit an entity to the database with error handling.
    
    Args:
        session: Database session
        entity: Entity to commit
        
    Returns:
        Any: The committed entity with refreshed data
        
    Raises:
        HTTPException 500: If database error occurs
    """
    try:
        session.add(entity)
        session.commit()
        session.refresh(entity)
        return entity
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed"
        )


def safe_delete(session: Session, entity: Any) -> bool:
    """
    Safely delete an entity from the database with error handling.
    
    Args:
        session: Database session
        entity: Entity to delete
        
    Returns:
        bool: True if successful
        
    Raises:
        HTTPException 500: If database error occurs
    """
    try:
        session.delete(entity)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete resource"
        )


def check_unique_constraint(
    session: Session,
    model_class: Any,
    field_name: str,
    field_value: Any,
    error_message: str,
    exclude_id: Optional[int] = None
) -> None:
    """
    Check if a field value is unique in the database.
    
    Args:
        session: Database session
        model_class: SQLModel class to check
        field_name: Name of the field to check
        field_value: Value to check for uniqueness
        error_message: Error message if not unique
        exclude_id: Optional ID to exclude from check (for updates)
        
    Raises:
        HTTPException 400: If value is not unique
    """
    from sqlmodel import select
    
    if field_value is None:
        return
    
    field = getattr(model_class, field_name)
    statement = select(model_class).where(field == field_value)
    
    if exclude_id:
        statement = statement.where(model_class.id != exclude_id)
    
    existing = session.exec(statement).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
