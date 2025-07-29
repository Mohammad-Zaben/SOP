"""
InvoiceItem SQLModel class representing the database table
Defines invoice item entity with fields: id, invoice_id, product_id, quantity, unit_price
"""
from typing import Optional

from sqlmodel import SQLModel, Field


class InvoiceItem(SQLModel, table=True):
    """Invoice item database model - details of each item in an invoice"""
    __tablename__ = "invoice_items"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_id: int = Field(foreign_key="invoices.id", index=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    quantity: int = Field(gt=0)  # Must be > 0
    unit_price: float = Field(ge=0.0)  # Snapshot of product price at time of sale, must be >= 0
