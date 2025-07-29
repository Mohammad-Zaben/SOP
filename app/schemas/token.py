"""
Token-related Pydantic schemas for authentication endpoints
Contains request/response schemas for JWT token operations
"""
from typing import Any, Dict

from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Response schema for authentication endpoints"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh endpoint"""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Response schema for refresh token endpoint"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
