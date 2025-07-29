"""
Invoice business logic layer
Handles invoice creation, calculation of totals, inventory updates, and sales processing
"""
from typing import List, Optional, Dict, Any

from fastapi import HTTPException, status
from sqlmodel import Session, select

from ..models.invoice import Invoice
from ..models.invoice_item import InvoiceItem
from ..models.product import Product
from ..models.user import User, UserRole
from ..schemas.invoice import InvoiceCreate
from ..schemas.invoice_item import InvoiceItemCreate
from ..utils.auth_utils import check_resource_ownership, check_admin_access, is_owner_or_admin
from ..utils.db_utils import handle_database_errors
from ..utils.datetime import parse_date_string, get_date_range_filter
from ..utils.validation_utils import validate_positive_number, validate_pagination_params
from .product_service import get_product_by_id


def create_invoice(session: Session, invoice_data: InvoiceCreate, current_user: User) -> Invoice:
    """
    Create a new invoice with automatic total calculation and inventory updates.
    
    Args:
        session: Database session
        invoice_data: Invoice creation data including items list
        current_user: Current authenticated user
        
    Returns:
        Invoice: Created invoice with all items
        
    Raises:
        HTTPException 400: If insufficient stock or invalid product
        HTTPException 403: If user is not authorized to sell these products
        HTTPException 500: If unexpected error occurs during creation
    """
    try:
        # Validate all products and check authorization before creating invoice
        validated_items = []
        total_price = 0.0
        
        for item_data in invoice_data.items:
            # Get product and validate existence
            product = get_product_by_id(session, item_data.product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product with ID {item_data.product_id} not found"
                )
            
            # Check authorization: user must own the product or be admin
            if current_user.role != UserRole.ADMIN and product.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Not authorized to sell product: {product.name}"
                )
            
            # Check stock availability
            if product.quantity < item_data.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for product {product.name}. Available: {product.quantity}, Requested: {item_data.quantity}"
                )
            
            # Calculate item total using current product price
            unit_price = item_data.unit_price if hasattr(item_data, 'unit_price') and item_data.unit_price else product.price
            item_total = unit_price * item_data.quantity
            total_price += item_total
            
            # Store validated item data
            validated_items.append({
                'product': product,
                'quantity': item_data.quantity,
                'unit_price': unit_price,
                'item_total': item_total
            })
        
        # Create the invoice
        db_invoice = Invoice(
            user_id=current_user.id,
            customer_name=invoice_data.customer_name,
            total_price=total_price
        )
        
        session.add(db_invoice)
        session.flush()  # Get invoice ID without committing
        
        # Create invoice items and update product quantities
        for item_info in validated_items:
            # Create invoice item
            db_invoice_item = InvoiceItem(
                invoice_id=db_invoice.id,
                product_id=item_info['product'].id,
                quantity=item_info['quantity'],
                unit_price=item_info['unit_price']
            )
            session.add(db_invoice_item)
            
            # Update product quantity (deduct sold quantity)
            item_info['product'].quantity -= item_info['quantity']
            session.add(item_info['product'])
        
        # Commit all changes
        session.commit()
        session.refresh(db_invoice)
        
        return db_invoice
        
    except HTTPException:
        # Re-raise HTTPExceptions (our custom validation errors)
        session.rollback()
        raise
    except Exception as e:
        # Handle any unexpected database or other errors
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the invoice."
        )


def get_invoice_by_id(session: Session, invoice_id: int, current_user: User) -> Optional[Invoice]:
    """
    Retrieve an invoice by ID with ownership check.
    
    Args:
        session: Database session
        invoice_id: Invoice ID to retrieve
        current_user: Current authenticated user
        
    Returns:
        Optional[Invoice]: Invoice if found and authorized
        
    Raises:
        HTTPException 404: If invoice not found
        HTTPException 403: If user is not authorized to view this invoice
    """
    # Get invoice
    statement = select(Invoice).where(Invoice.id == invoice_id)
    invoice = session.exec(statement).first()
    
    # Check ownership and return
    return check_resource_ownership(current_user, invoice, "invoice")


def get_all_invoices(
    session: Session, 
    current_user: User, 
    skip: int = 0, 
    limit: int = 100
) -> List[Invoice]:
    """
    Get all invoices with role-based filtering and pagination.
    Admin sees all invoices, regular users see only their own.
    
    Args:
        session: Database session
        current_user: Current authenticated user
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        
    Returns:
        List[Invoice]: List of invoices based on user role
    """
    # Validate pagination parameters
    validate_pagination_params(skip, limit)
    
    statement = select(Invoice)
    
    # Restrict to user's invoices unless admin
    if not is_owner_or_admin(current_user, current_user.id):
        statement = statement.where(Invoice.user_id == current_user.id)
    
    # Apply pagination and ordering
    statement = statement.offset(skip).limit(limit)
    statement = statement.order_by(Invoice.created_at.desc())
    
    return session.exec(statement).all()


def get_invoices_by_user_id(
    session: Session, 
    user_id: int, 
    current_user: User,
    skip: int = 0,
    limit: int = 100
) -> List[Invoice]:
    """
    Get all invoices for a specific user (admin only feature).
    
    Args:
        session: Database session
        user_id: ID of user whose invoices to retrieve
        current_user: Current authenticated user (must be admin)
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        
    Returns:
        List[Invoice]: List of user's invoices
        
    Raises:
        HTTPException 403: If current user is not admin
    """
    # Check admin access
    check_admin_access(current_user, "view other users' invoices")
    
    # Validate pagination
    validate_pagination_params(skip, limit)
    
    statement = select(Invoice).where(Invoice.user_id == user_id)
    statement = statement.offset(skip).limit(limit)
    statement = statement.order_by(Invoice.created_at.desc())
    
    return session.exec(statement).all()


def get_invoice_items(session: Session, invoice_id: int, current_user: User) -> List[InvoiceItem]:
    """
    Get all items for a specific invoice with authorization check.
    
    Args:
        session: Database session
        invoice_id: Invoice ID
        current_user: Current authenticated user
        
    Returns:
        List[InvoiceItem]: List of invoice items
        
    Raises:
        HTTPException 404: If invoice not found
        HTTPException 403: If user is not authorized
    """
    # First verify access to the invoice
    invoice = get_invoice_by_id(session, invoice_id, current_user)
    
    # Get invoice items
    statement = select(InvoiceItem).where(InvoiceItem.invoice_id == invoice_id)
    return session.exec(statement).all()


def get_sales_summary(
    session: Session, 
    current_user: User,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get sales summary statistics for the user or all users (if admin).
    
    Args:
        session: Database session
        current_user: Current authenticated user
        start_date: Optional start date filter (ISO format)
        end_date: Optional end date filter (ISO format)
        
    Returns:
        Dict[str, Any]: Sales summary with total revenue, invoice count, etc.
    """
    from datetime import datetime
    from sqlmodel import func
    
    statement = select(
        func.count(Invoice.id).label('total_invoices'),
        func.sum(Invoice.total_price).label('total_revenue'),
        func.avg(Invoice.total_price).label('average_invoice_value')
    )
    
    # Filter by user unless admin
    if current_user.role != UserRole.ADMIN:
        statement = statement.where(Invoice.user_id == current_user.id)
    
    # Apply date filters if provided
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            statement = statement.where(Invoice.created_at >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            statement = statement.where(Invoice.created_at <= end_dt)
        except ValueError:
            pass
    
    result = session.exec(statement).first()
    
    return {
        'total_invoices': result.total_invoices or 0,
        'total_revenue': float(result.total_revenue or 0),
        'average_invoice_value': float(result.average_invoice_value or 0)
    }


def search_invoices(
    session: Session,
    filters: Dict[str, Any],
    current_user: User,
    skip: int = 0,
    limit: int = 100
) -> List[Invoice]:
    """
    Search invoices with various filters.
    
    Args:
        session: Database session
        filters: Dictionary containing search criteria:
            - customer_name: partial match
            - min_total: minimum total price
            - max_total: maximum total price
            - start_date: start date filter
            - end_date: end date filter
        current_user: Current authenticated user
        skip: Pagination offset
        limit: Pagination limit
        
    Returns:
        List[Invoice]: List of matching invoices
    """
    # Validate pagination
    validate_pagination_params(skip, limit)
    
    statement = select(Invoice)
    
    # Restrict to user's invoices unless admin
    if not is_owner_or_admin(current_user, current_user.id):
        statement = statement.where(Invoice.user_id == current_user.id)
    
    # Apply filters
    if "customer_name" in filters and filters["customer_name"]:
        statement = statement.where(Invoice.customer_name.ilike(f"%{filters['customer_name']}%"))
    
    if "min_total" in filters and filters["min_total"] is not None:
        statement = statement.where(Invoice.total_price >= filters["min_total"])
    
    if "max_total" in filters and filters["max_total"] is not None:
        statement = statement.where(Invoice.total_price <= filters["max_total"])
    
    # Use date utility for parsing date filters
    start_dt, end_dt = get_date_range_filter(
        filters.get("start_date"), 
        filters.get("end_date")
    )
    
    if start_dt:
        statement = statement.where(Invoice.created_at >= start_dt)
    
    if end_dt:
        statement = statement.where(Invoice.created_at <= end_dt)
    
    # Apply pagination and ordering
    statement = statement.offset(skip).limit(limit)
    statement = statement.order_by(Invoice.created_at.desc())
    
    return session.exec(statement).all()
