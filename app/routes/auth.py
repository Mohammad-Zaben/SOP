"""
Authentication API routes
Handles user login, token refresh, and user profile endpoints for the POS SaaS system
"""
from datetime import timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from ..core.config import get_settings
from ..core.database import get_session
from ..core.security import create_access_token, verify_password, decode_access_token
from ..dependencies.auth import get_active_user
from ..models.user import User, UserStatus
from ..schemas.user import UserRead
from ..schemas.token import TokenResponse, RefreshTokenRequest, RefreshTokenResponse
from ..services.user_service import get_user_by_username, get_user_by_id


# Initialize router and settings
router = APIRouter()
settings = get_settings()


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
) -> TokenResponse:
    """
    Authenticate user with username and password, return access and refresh tokens.
    
    Args:
        form_data: OAuth2 form data containing username and password
        session: Database session dependency
        
    Returns:
        TokenResponse: Contains access token, refresh token, and user info
        
    Raises:
        HTTPException 401: If credentials are invalid
        HTTPException 403: If user account is not active
    """
    # Authenticate user credentials
    user = get_user_by_username(session, form_data.username)
    
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status.value}. Please contact administrator.",
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )
    
    # Create refresh token (longer expiration)
    refresh_token_expires = timedelta(days=7)  # 7 days for refresh token
    refresh_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "type": "refresh"},
        expires_delta=refresh_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": user.id,
            "username": user.username,
            "role": user.role.value,
            "status": user.status.value,
            "shop_type": user.shop_type,
            "email": user.email
        }
    )


@router.post("/refresh", response_model=RefreshTokenResponse, status_code=status.HTTP_200_OK)
def refresh_access_token(
    refresh_request: RefreshTokenRequest,
    session: Session = Depends(get_session)
) -> RefreshTokenResponse:
    """
    Generate new access token using valid refresh token.
    
    Args:
        refresh_request: Request containing refresh token
        session: Database session dependency
        
    Returns:
        RefreshTokenResponse: New access token with expiration info
        
    Raises:
        HTTPException 401: If refresh token is invalid or expired
        HTTPException 403: If user is no longer active
    """
    try:
        # Decode refresh token
        payload = decode_access_token(refresh_request.refresh_token)
        
        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Extract user ID
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Get user and validate still active
        user = get_user_by_id(session, int(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {user.status.value}. Please contact administrator."
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username},
            expires_delta=access_token_expires
        )
        
        return RefreshTokenResponse(
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )


@router.get("/me", response_model=UserRead, status_code=status.HTTP_200_OK)
def get_current_user_profile(
    current_user: User = Depends(get_active_user)
) -> UserRead:
    """
    Get the currently authenticated user's profile information.
    
    Args:
        current_user: Current authenticated and active user from dependency
        
    Returns:
        UserRead: Current user's profile data
    """
    return UserRead(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        phone=current_user.phone,
        shop_type=current_user.shop_type,
        location=current_user.location,
        role=current_user.role.value,
        status=current_user.status.value,
        created_at=current_user.created_at
    )
