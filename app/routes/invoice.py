"""
Invoice and sales API routes
Handles POS sales operations, invoice creation, and sales history endpoints
"""
from typing import List, Dict, Any, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session

from ..core.database import get_session
from ..dependencies.auth import get_active_user, get_current_admin
from ..models.user import User
from ..schemas.invoice import InvoiceCreate, InvoiceRead
from ..services import invoice_service


router = APIRouter()


@router.post("/", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED, summary="Create new invoice")
def create_invoice(
    invoice_data: InvoiceCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_active_user)
) -> InvoiceRead:
    """
    Create invoice (authenticated user only, triggers stock deduction).
    
    Args:
        invoice_data: Invoice creation data from InvoiceCreate schema
        session: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        InvoiceRead: Created invoice with items
        
    Raises:
        HTTPException 400: If product not found or insufficient stock
        HTTPException 403: If trying to use another user's product
    """
    created_invoice = invoice_service.create_invoice(session, invoice_data, current_user)
    return InvoiceRead.from_orm(created_invoice)


@router.get("/summary", status_code=status.HTTP_200_OK, summary="Get sales summary")
def get_sales_summary(
    start_date: Optional[date] = Query(None, description="Start date for summary period"),
    end_date: Optional[date] = Query(None, description="End date for summary period"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_active_user)
) -> Dict[str, Any]:
    """
    Sales summary report for the current user.
    
    Args:
        start_date: Optional start date for summary period
        end_date: Optional end date for summary period
        session: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Sales summary with totals and counts
        
    Raises:
        HTTPException 400: If date range is invalid
    """
    # Validate date range
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date cannot be after end date"
        )
    
    # Get sales summary
    summary = invoice_service.get_sales_summary(session, current_user.id, start_date, end_date)
    
    return summary


@router.get("/{invoice_id}", response_model=InvoiceRead, status_code=status.HTTP_200_OK, summary="Get invoice by ID")
def get_invoice_by_id(
    invoice_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_active_user)
) -> InvoiceRead:
    """
    Get invoice with items (owner or admin only).
    
    Args:
        invoice_id: ID of the invoice to retrieve
        session: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        InvoiceRead: Invoice data with items
        
    Raises:
        HTTPException 403: If user tries to access another user's invoice
        HTTPException 404: If invoice not found
    """
    invoice = invoice_service.get_invoice_by_id(session, invoice_id, current_user)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    return InvoiceRead.from_orm(invoice)


@router.get("/", response_model=List[InvoiceRead], status_code=status.HTTP_200_OK, summary="Search invoices with filters")
def search_invoices(
    start_date: Optional[date] = Query(None, description="Start date for date range filter"),
    end_date: Optional[date] = Query(None, description="End date for date range filter"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum total price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum total price filter"),
    customer_name: Optional[str] = Query(None, description="Filter by customer name (partial match)"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_active_user)
) -> List[InvoiceRead]:
    """
    Search invoices with date range and price range filters.
    
    Args:
        start_date: Optional start date filter
        end_date: Optional end date filter
        min_price: Optional minimum price filter
        max_price: Optional maximum price filter
        customer_name: Optional customer name filter
        session: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        List[InvoiceRead]: List of invoices matching the filters
        
    Raises:
        HTTPException 400: If date range or price range is invalid
    """
    # Build filters dictionary using dictionary comprehension
    filters = {k: v for k, v in {
        "start_date": start_date,
        "end_date": end_date,
        "min_price": min_price,
        "max_price": max_price,
        "customer_name": customer_name,
    }.items() if v is not None}
    
    # Validate price range
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum price cannot be greater than maximum price"
        )
    
    # Validate date range
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date cannot be after end date"
        )
    
    # Get invoices based on filters
    invoices = invoice_service.search_invoices(session, filters, current_user)
    
    return [InvoiceRead.from_orm(invoice) for invoice in invoices]
