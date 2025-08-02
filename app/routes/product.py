"""
Product management API routes
Handles product CRUD operations, inventory management, and search functionality
"""
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session

from ..core.database import get_session
from ..dependencies.auth import get_active_user, get_current_admin
from ..models.user import User
from ..schemas.product import ProductCreate, ProductRead, ProductUpdate
from ..services import product_service


router = APIRouter()


@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED, summary="Create new product")
def create_product(
    product_data: ProductCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_active_user)
) -> ProductRead:
    """
    Create a new product (authenticated user only).
    
    Args:
        product_data: Product creation data from ProductCreate schema
        session: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        ProductRead: Created product data
        
    Raises:
        HTTPException 400: If barcode already exists for the user
    """
    created_product = product_service.create_product(session, current_user.id, product_data)
    return ProductRead.from_orm(created_product)


@router.get("/{product_id}", response_model=ProductRead, status_code=status.HTTP_200_OK, summary="Get product by ID")
def get_product_by_id(
    product_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_active_user)
) -> ProductRead:
    """
    Get product by ID (must belong to user or admin).
    
    Args:
        product_id: ID of the product to retrieve
        session: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        ProductRead: Product data
        
    Raises:
        HTTPException 403: If user tries to access another user's product
        HTTPException 404: If product not found
    """
    product = product_service.get_product_by_id(session, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # IDOR protection: users can only access their own products unless admin
    from ..models.user import UserRole
    if current_user.role != UserRole.ADMIN and product.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only access your own products."
        )
    
    return ProductRead.from_orm(product)


@router.put("/{product_id}", response_model=ProductRead, status_code=status.HTTP_200_OK, summary="Update product")
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_active_user)
) -> ProductRead:
    """
    Update product (owner or admin only).
    
    Args:
        product_id: ID of the product to update
        product_update: Product update data from ProductUpdate schema
        session: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        ProductRead: Updated product data
        
    Raises:
        HTTPException 403: If user tries to update another user's product
        HTTPException 404: If product not found
    """
    updated_product = product_service.update_product(session, product_id, product_update, current_user)
    if not updated_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return ProductRead.from_orm(updated_product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete product")
def delete_product(
    product_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_active_user)
) -> None:
    """
    Delete product (owner or admin only).
    
    Args:
        product_id: ID of the product to delete
        session: Database session dependency
        current_user: Current authenticated user
        
    Raises:
        HTTPException 403: If user tries to delete another user's product
        HTTPException 404: If product not found
    """
    success = product_service.delete_product(session, product_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )


@router.get("/low-stock", response_model=List[ProductRead], status_code=status.HTTP_200_OK, summary="Get low stock products")
def get_low_stock_products(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_active_user)
) -> List[ProductRead]:
    """
    List products below threshold for the current user.
    
    Args:
        session: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        List[ProductRead]: List of low-stock products
    """
    low_stock_products = product_service.get_low_stock_products(session, current_user.id)
    
    return [ProductRead.from_orm(product) for product in low_stock_products]


@router.get("/", response_model=List[ProductRead], status_code=status.HTTP_200_OK, summary="Search products by name or category")
def search_products(
    name: Optional[str] = Query(None, description="Filter by product name (partial match)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    barcode: Optional[str] = Query(None, description="Filter by barcode"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_active_user)
) -> List[ProductRead]:
    """
    Search/filter products by name, category, or barcode.
    
    Args:
        name: Optional name filter (partial match)
        category: Optional category filter
        barcode: Optional barcode filter
        session: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        List[ProductRead]: List of products matching the filters
    """
    # Build filters dictionary using dictionary comprehension
    filters = {k: v for k, v in {
        "name": name,
        "category": category,
        "barcode": barcode,
    }.items() if v is not None}
    
    # Get products based on filters
    products = product_service.search_products(session, filters, current_user)
    
    return [ProductRead.from_orm(product) for product in products]


@router.get("/user/products", response_model=List[ProductRead], status_code=status.HTTP_200_OK, summary="Get all products for current user")
def get_user_products(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_active_user)
) -> List[ProductRead]:
    """
    Get all products belonging to the current user.
    
    Args:
        session: Database session dependency
        current_user: Current authenticated user
        
    Returns:
        List[ProductRead]: List of all user's products
    """
    user_products = product_service.get_user_products(session, current_user.id)
    
    return [ProductRead.from_orm(product) for product in user_products]
