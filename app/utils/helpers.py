"""
Common reusable utility functions
Contains general-purpose helper functions used across the application
"""
from typing import Dict, Any, List, Optional, Union
from sqlmodel import Session, select


def build_filter_query(base_query, model_class: Any, filters: Dict[str, Any]) -> Any:
    """
    Build dynamic filter query from filter dictionary.
    
    Args:
        base_query: Base SQLModel select query
        model_class: SQLModel class to filter
        filters: Dictionary of filters
        
    Returns:
        Modified query with filters applied
    """
    query = base_query
    
    for field_name, field_value in filters.items():
        if field_value is not None and field_value != "":
            if hasattr(model_class, field_name):
                field = getattr(model_class, field_name)
                
                # Handle different filter types
                if field_name.endswith('_like') or field_name in ['name', 'username', 'location', 'customer_name']:
                    # Partial match for text fields
                    query = query.where(field.ilike(f"%{field_value}%"))
                elif field_name.startswith('min_'):
                    # Minimum value filter
                    actual_field = field_name[4:]  # Remove 'min_' prefix
                    if hasattr(model_class, actual_field):
                        actual_field_obj = getattr(model_class, actual_field)
                        query = query.where(actual_field_obj >= field_value)
                elif field_name.startswith('max_'):
                    # Maximum value filter
                    actual_field = field_name[4:]  # Remove 'max_' prefix
                    if hasattr(model_class, actual_field):
                        actual_field_obj = getattr(model_class, actual_field)
                        query = query.where(actual_field_obj <= field_value)
                else:
                    # Exact match
                    query = query.where(field == field_value)
    
    return query


def calculate_pagination_offset(page: int, page_size: int) -> int:
    """
    Calculate offset for pagination.
    
    Args:
        page: Page number (1-based)
        page_size: Number of items per page
        
    Returns:
        int: Offset for database query
    """
    return (page - 1) * page_size


def create_pagination_info(
    total_items: int, 
    page: int, 
    page_size: int
) -> Dict[str, Any]:
    """
    Create pagination metadata.
    
    Args:
        total_items: Total number of items
        page: Current page number
        page_size: Items per page
        
    Returns:
        Dict: Pagination information
    """
    total_pages = (total_items + page_size - 1) // page_size
    
    return {
        "total_items": total_items,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1
    }


def format_currency(amount: float, currency: str = "SAR") -> str:
    """
    Format currency amount for display.
    
    Args:
        amount: Amount to format
        currency: Currency code
        
    Returns:
        str: Formatted currency string
    """
    return f"{amount:.2f} {currency}"


def sanitize_string(text: Optional[str]) -> Optional[str]:
    """
    Sanitize string input by removing extra whitespace.
    
    Args:
        text: String to sanitize
        
    Returns:
        Optional[str]: Sanitized string or None
    """
    if text is None:
        return None
    
    sanitized = text.strip()
    return sanitized if sanitized else None


def extract_numbers_from_string(text: str) -> List[int]:
    """
    Extract all numbers from a string.
    
    Args:
        text: String to extract numbers from
        
    Returns:
        List[int]: List of extracted numbers
    """
    import re
    return [int(x) for x in re.findall(r'\d+', text)]


def generate_unique_code(prefix: str = "", length: int = 8) -> str:
    """
    Generate a unique alphanumeric code.
    
    Args:
        prefix: Optional prefix for the code
        length: Length of the random part
        
    Returns:
        str: Generated unique code
    """
    import random
    import string
    
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return f"{prefix}{random_part}" if prefix else random_part


def safe_divide(numerator: Union[int, float], denominator: Union[int, float]) -> float:
    """
    Safely divide two numbers, returning 0 if denominator is 0.
    
    Args:
        numerator: Numerator
        denominator: Denominator
        
    Returns:
        float: Division result or 0 if division by zero
    """
    return numerator / denominator if denominator != 0 else 0.0


def group_by_field(items: List[Any], field_name: str) -> Dict[Any, List[Any]]:
    """
    Group a list of objects by a specific field.
    
    Args:
        items: List of objects to group
        field_name: Name of the field to group by
        
    Returns:
        Dict: Dictionary with field values as keys and lists of objects as values
    """
    grouped = {}
    for item in items:
        key = getattr(item, field_name, None)
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(item)
    
    return grouped
