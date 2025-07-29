"""
Date and time formatting utilities
Contains helper functions for datetime operations, formatting, and timezone handling
"""
from datetime import datetime, date
from typing import Optional

from fastapi import HTTPException, status


def parse_date_string(date_string: Optional[str], field_name: str = "date") -> Optional[datetime]:
    """
    Parse ISO format date string to datetime object.
    
    Args:
        date_string: ISO format date string
        field_name: Name of the field for error message
        
    Returns:
        Optional[datetime]: Parsed datetime or None if input is None
        
    Raises:
        HTTPException 400: If date format is invalid
    """
    if not date_string:
        return None
    
    try:
        return datetime.fromisoformat(date_string)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name} format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
        )


def format_datetime(dt: datetime, format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object to string.
    
    Args:
        dt: Datetime object to format
        format_string: Format string (default: YYYY-MM-DD HH:MM:SS)
        
    Returns:
        str: Formatted datetime string
    """
    return dt.strftime(format_string)


def get_date_range_filter(
    start_date: Optional[str], 
    end_date: Optional[str]
) -> tuple[Optional[datetime], Optional[datetime]]:
    """
    Parse and validate date range parameters.
    
    Args:
        start_date: Start date string in ISO format
        end_date: End date string in ISO format
        
    Returns:
        tuple: (start_datetime, end_datetime) or (None, None) if no dates provided
        
    Raises:
        HTTPException 400: If date format is invalid or range is invalid
    """
    start_dt = parse_date_string(start_date, "start_date")
    end_dt = parse_date_string(end_date, "end_date")
    
    # Validate date range
    if start_dt and end_dt and start_dt > end_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date"
        )
    
    return start_dt, end_dt


def is_today(dt: datetime) -> bool:
    """
    Check if datetime is today.
    
    Args:
        dt: Datetime to check
        
    Returns:
        bool: True if datetime is today
    """
    return dt.date() == date.today()


def days_between(start: datetime, end: datetime) -> int:
    """
    Calculate number of days between two dates.
    
    Args:
        start: Start datetime
        end: End datetime
        
    Returns:
        int: Number of days between dates
    """
    return (end.date() - start.date()).days


def get_current_timestamp() -> datetime:
    """
    Get current UTC timestamp.
    
    Returns:
        datetime: Current UTC datetime
    """
    return datetime.utcnow()
