"""
Product Pydantic DTOs for request/response schemas
Contains ProductCreate, ProductRead, ProductUpdate schemas for API validation and serialization
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class ProductBase(BaseModel):
    """Base product schema with common fields"""
    name: str = Field(min_length=1, max_length=200)
    barcode: str = Field(min_length=1, max_length=50)
    category: Optional[str] = Field(None, max_length=100)
    quantity: int = Field(ge=0)
    price: float = Field(ge=0.0)
    threshold: int = Field(default=0, ge=0)
    description: Optional[str] = Field(None, max_length=500)


class ProductCreate(ProductBase):
    """Schema for creating a new product"""
    pass


class ProductRead(ProductBase):
    """Schema for reading product data (response model)"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProductUpdate(BaseModel):
    """Schema for updating product data (partial update)"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    barcode: Optional[str] = Field(None, min_length=1, max_length=50)
    category: Optional[str] = Field(None, max_length=100)
    quantity: Optional[int] = Field(None, ge=0)
    price: Optional[float] = Field(None, ge=0.0)
    threshold: Optional[int] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=500)
    
    @validator('quantity', 'threshold')
    def validate_non_negative_integers(cls, v):
        if v is not None and v < 0:
            raise ValueError('Value must be >= 0')
        return v
    
    @validator('price')
    def validate_non_negative_price(cls, v):
        if v is not None and v < 0.0:
            raise ValueError('Price must be >= 0')
        return v
