"""
Validation utilities for common business rules and data validation
Contains reusable validation functions used across the application
"""
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import HTTPException, status


def validate_positive_number(value: Any, field_name: str) -> None:
    """
    Validate that a number is positive.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error message
        
    Raises:
        HTTPException 400: If value is not positive
    """
    if value is not None and value <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be greater than 0"
        )


def validate_non_negative_number(value: Any, field_name: str) -> None:
    """
    Validate that a number is non-negative.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error message
        
    Raises:
        HTTPException 400: If value is negative
    """
    if value is not None and value < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be greater than or equal to 0"
        )


def validate_enum_value(value: Any, valid_values: List[str], field_name: str) -> None:
    """
    Validate that a value is in the allowed enum values.
    
    Args:
        value: Value to validate
        valid_values: List of valid enum values
        field_name: Name of the field for error message
        
    Raises:
        HTTPException 400: If value is not in valid values
    """
    if value is not None and value not in valid_values:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name}. Must be one of: {', '.join(valid_values)}"
        )


def validate_required_field(value: Any, field_name: str) -> None:
    """
    Validate that a required field is provided.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error message
        
    Raises:
        HTTPException 400: If value is None or empty
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} is required"
        )


def validate_string_length(
    value: Optional[str], 
    field_name: str, 
    min_length: Optional[int] = None,
    max_length: Optional[int] = None
) -> None:
    """
    Validate string length constraints.
    
    Args:
        value: String value to validate
        field_name: Name of the field for error message
        min_length: Minimum required length
        max_length: Maximum allowed length
        
    Raises:
        HTTPException 400: If length constraints are violated
    """
    if value is None:
        return
    
    if min_length is not None and len(value) < min_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be at least {min_length} characters long"
        )
    
    if max_length is not None and len(value) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be no more than {max_length} characters long"
        )


def validate_phone_number(phone: Optional[str]) -> None:
    """
    Validate phone number format (Saudi format: 05xxxxxxxx).
    
    Args:
        phone: Phone number to validate
        
    Raises:
        HTTPException 400: If phone format is invalid
    """
    import re
    
    if phone is None:
        return
    
    pattern = r"^05\d{8}$"
    if not re.match(pattern, phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number must be in format 05xxxxxxxx"
        )


def validate_email_format(email: Optional[str]) -> None:
    """
    Validate email format.
    
    Args:
        email: Email to validate
        
    Raises:
        HTTPException 400: If email format is invalid
    """
    import re
    
    if email is None:
        return
    
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )


def validate_pagination_params(skip: int, limit: int) -> None:
    """
    Validate pagination parameters.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Raises:
        HTTPException 400: If pagination parameters are invalid
    """
    if skip < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skip parameter must be non-negative"
        )
    
    if limit <= 0 or limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit parameter must be between 1 and 1000"
        )
