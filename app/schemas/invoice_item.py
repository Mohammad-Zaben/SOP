"""
InvoiceItem Pydantic DTOs for request/response schemas
Contains InvoiceItemCreate, InvoiceItemRead schemas for API validation and serialization
"""
from pydantic import BaseModel, Field, validator


class InvoiceItemBase(BaseModel):
    """Base invoice item schema with common fields"""
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0.0)


class InvoiceItemCreate(InvoiceItemBase):
    """Schema for creating a new invoice item"""
    pass


class InvoiceItemRead(InvoiceItemBase):
    """Schema for reading invoice item data (response model)"""
    
    class Config:
        orm_mode = True
