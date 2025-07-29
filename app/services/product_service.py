"""
Product business logic layer
Handles product CRUD operations, inventory management, and user-specific product filtering
"""
from typing import List, Optional, Dict, Any

from fastapi import HTTPException, status
from sqlmodel import Session, select

from ..models.product import Product
from ..models.user import User, UserRole
from ..schemas.product import ProductCreate, ProductUpdate
from ..utils.auth_utils import check_resource_ownership, is_owner_or_admin
from ..utils.db_utils import check_unique_constraint, handle_database_errors, safe_commit, safe_delete
from ..utils.validation_utils import validate_positive_number, validate_non_negative_number


@handle_database_errors("product creation")
def create_product(session: Session, user_id: int, product_data: ProductCreate) -> Product:
    """
    Create a new product and associate it with the specified user.
    
    Args:
        session: Database session
        user_id: ID of the user who owns this product
        product_data: Product creation data from ProductCreate schema
        
    Returns:
        Product: Created product instance
        
    Raises:
        HTTPException 400: If barcode already exists
        HTTPException 500: If unexpected error occurs during creation
    """
    # Check barcode uniqueness
    check_unique_constraint(
        session, Product, "barcode", product_data.barcode, 
        "Product with this barcode already exists"
    )
    
    # Validate numeric fields
    validate_non_negative_number(product_data.quantity, "quantity")
    validate_non_negative_number(product_data.price, "price")
    validate_non_negative_number(product_data.threshold, "threshold")
    
    # Create product instance
    db_product = Product(
        user_id=user_id,
        name=product_data.name,
        barcode=product_data.barcode,
        category=product_data.category,
        quantity=product_data.quantity,
        price=product_data.price,
        threshold=product_data.threshold,
        description=product_data.description
    )
    
    return safe_commit(session, db_product)


def get_product_by_id(session: Session, product_id: int) -> Optional[Product]:
    """
    Retrieve a product by its ID.
    
    Args:
        session: Database session
        product_id: Product ID to search for
        
    Returns:
        Optional[Product]: Product instance if found, None otherwise
    """
    statement = select(Product).where(Product.id == product_id)
    return session.exec(statement).first()


def update_product(session: Session, product_id: int, product_data: ProductUpdate, current_user: User) -> Optional[Product]:
    """
    Update product fields. Restrict to owners or admins only.
    
    Args:
        session: Database session
        product_id: ID of product to update
        product_data: Update data from ProductUpdate schema
        current_user: Current authenticated user
        
    Returns:
        Optional[Product]: Updated product instance if found and authorized, None otherwise
        
    Raises:
        HTTPException 404: If product not found
        HTTPException 403: If user is not authorized to update this product
        HTTPException 400: If barcode conflicts with existing product
    """
    # Get product and check ownership
    product = get_product_by_id(session, product_id)
    check_resource_ownership(current_user, product, "product")
    
    try:
        # Get update data
        update_data = product_data.dict(exclude_unset=True)
        
        # Check barcode uniqueness if being updated
        if "barcode" in update_data and update_data["barcode"] != product.barcode:
            check_unique_constraint(
                session, Product, "barcode", update_data["barcode"],
                "Product with this barcode already exists", exclude_id=product_id
            )
        
        # Validate numeric fields if being updated
        if "quantity" in update_data:
            validate_non_negative_number(update_data["quantity"], "quantity")
        if "price" in update_data:
            validate_non_negative_number(update_data["price"], "price")
        if "threshold" in update_data:
            validate_non_negative_number(update_data["threshold"], "threshold")
        
        # Update fields
        for field, value in update_data.items():
            setattr(product, field, value)
        
        return safe_commit(session, product)
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating the product."
        )


def delete_product(session: Session, product_id: int, current_user: User) -> bool:
    """
    Delete a product if the current_user is the owner or admin.
    
    Args:
        session: Database session
        product_id: ID of product to delete
        current_user: Current authenticated user
        
    Returns:
        bool: True if product was deleted
        
    Raises:
        HTTPException 404: If product not found
        HTTPException 403: If user is not authorized to delete this product
    """
    # Get product and check ownership
    product = get_product_by_id(session, product_id)
    check_resource_ownership(current_user, product, "product")
    
    return safe_delete(session, product)


def get_user_products(session: Session, user_id: int) -> List[Product]:
    """
    Get all products for a specific user.
    
    Args:
        session: Database session
        user_id: ID of the user whose products to retrieve
        
    Returns:
        List[Product]: List of user's products (may be empty)
    """
    statement = select(Product).where(Product.user_id == user_id)
    return session.exec(statement).all()


def search_products(session: Session, filters: Dict[str, Any], current_user: User) -> List[Product]:
    """
    Search products using various filters. Regular users see only their products, admins see all.
    
    Args:
        session: Database session
        filters: Dictionary containing search criteria:
            - name: partial match (case-insensitive)
            - min_price: minimum price filter
            - max_price: maximum price filter
            - category: exact match
            - min_quantity: minimum quantity available
            - max_quantity: maximum quantity available
            - barcode: exact match
        current_user: Current authenticated user
        
    Returns:
        List[Product]: List of matching products (may be empty)
    """
    statement = select(Product)
    
    # Restrict to user's products unless admin
    if current_user.role != UserRole.ADMIN:
        statement = statement.where(Product.user_id == current_user.id)
    
    # Apply filters dynamically
    if "name" in filters and filters["name"]:
        statement = statement.where(Product.name.ilike(f"%{filters['name']}%"))
    
    if "min_price" in filters and filters["min_price"] is not None:
        statement = statement.where(Product.price >= filters["min_price"])
    
    if "max_price" in filters and filters["max_price"] is not None:
        statement = statement.where(Product.price <= filters["max_price"])
    
    if "category" in filters and filters["category"]:
        statement = statement.where(Product.category == filters["category"])
    
    if "min_quantity" in filters and filters["min_quantity"] is not None:
        statement = statement.where(Product.quantity >= filters["min_quantity"])
    
    if "max_quantity" in filters and filters["max_quantity"] is not None:
        statement = statement.where(Product.quantity <= filters["max_quantity"])
    
    if "barcode" in filters and filters["barcode"]:
        statement = statement.where(Product.barcode == filters["barcode"])
    
    return session.exec(statement).all()


def get_product_by_barcode(session: Session, barcode: str) -> Optional[Product]:
    """
    Retrieve a product by its barcode.
    
    Args:
        session: Database session
        barcode: Barcode to search for
        
    Returns:
        Optional[Product]: Product instance if found, None otherwise
    """
    statement = select(Product).where(Product.barcode == barcode)
    return session.exec(statement).first()


def get_low_stock_products(session: Session, user_id: int) -> List[Product]:
    """
    Get products that are running low on stock (quantity <= threshold).
    
    Args:
        session: Database session
        user_id: ID of the user whose products to check
        
    Returns:
        List[Product]: List of products running low on stock
    """
    statement = select(Product).where(
        Product.user_id == user_id,
        Product.quantity <= Product.threshold
    )
    return session.exec(statement).all()


def update_product_quantity(session: Session, product_id: int, quantity_change: int, current_user: User) -> Optional[Product]:
    """
    Update product quantity (for sales or restocking).
    
    Args:
        session: Database session
        product_id: ID of product to update
        quantity_change: Change in quantity (negative for sales, positive for restocking)
        current_user: Current authenticated user
        
    Returns:
        Optional[Product]: Updated product instance
        
    Raises:
        HTTPException 404: If product not found
        HTTPException 403: If user is not authorized
        HTTPException 400: If insufficient stock for sale
    """
    # Get existing product
    product = get_product_by_id(session, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check ownership or admin permission
    if current_user.role != UserRole.ADMIN and product.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this product"
        )
    
    # Calculate new quantity
    new_quantity = product.quantity + quantity_change
    
    # Check for sufficient stock (only for negative changes - sales)
    if new_quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock for this operation"
        )
    
    try:
        # Update quantity
        product.quantity = new_quantity
        session.add(product)
        session.commit()
        session.refresh(product)
        
        return product
        
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating product quantity."
        )
