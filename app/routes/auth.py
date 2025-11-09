"""
API routes for authentication operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import UserCreate, UserLogin, UserResponse, Token, RefreshTokenRequest
from app.services.auth import auth_service
from app.utils.logger import get_logger

logger = get_logger("auth_routes")

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password"
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account.

    Args:
        user_data: User registration data (email and password)
        db: Database session

    Returns:
        UserResponse with created user information

    Raises:
        HTTPException: If email already exists or registration fails
    """
    logger.info(f"Registration attempt", email=user_data.email)

    user = await auth_service.register_user(db, user_data)
    await db.commit()

    logger.info(f"User registered successfully", user_id=str(user.id), email=user.email)

    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=Token,
    summary="Login user",
    description="Authenticate user and receive access and refresh tokens"
)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and generate JWT tokens.

    Args:
        login_data: User login credentials (email and password)
        db: Database session

    Returns:
        Token with access_token and refresh_token

    Raises:
        HTTPException: If credentials are invalid
    """
    logger.info(f"Login attempt", email=login_data.email)

    token = await auth_service.authenticate_user(db, login_data)

    logger.info(f"User logged in successfully", email=login_data.email)

    return token


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Generate new access and refresh tokens using a valid refresh token"
)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using a refresh token.

    Args:
        refresh_data: Refresh token request with refresh_token
        db: Database session

    Returns:
        Token with new access_token and refresh_token

    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    logger.info("Token refresh attempt")

    token = await auth_service.refresh_access_token(db, refresh_data.refresh_token)

    logger.info("Token refreshed successfully")

    return token
