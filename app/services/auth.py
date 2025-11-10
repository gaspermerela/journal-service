"""
Authentication service for user registration, login, and token management.
"""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError

from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, Token
from app.services.database import db_service
from app.utils.security import verify_password
from app.utils.jwt import create_access_token, create_refresh_token, verify_token
from app.utils.logger import get_logger

logger = get_logger("auth_service")


class AuthService:
    """Service for authentication operations."""

    async def register_user(
        self,
        db: AsyncSession,
        user_data: UserCreate
    ) -> User:
        """
        Register a new user.

        Args:
            db: Database session
            user_data: User registration data

        Returns:
            Created User instance

        Raises:
            HTTPException: If registration fails
        """
        try:
            user = await db_service.create_user(db, user_data)
            logger.info(f"User registered successfully", user_id=str(user.id), email=user.email)
            return user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"User registration failed",
                email=user_data.email,
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed"
            )

    async def authenticate_user(
        self,
        db: AsyncSession,
        login_data: UserLogin
    ) -> Token:
        """
        Authenticate a user and generate access/refresh tokens.

        Args:
            db: Database session
            login_data: User login credentials

        Returns:
            Token object with access and refresh tokens

        Raises:
            HTTPException: If authentication fails
        """
        try:
            # Get user by email
            user = await db_service.get_user_by_email(db, login_data.email)

            if not user:
                logger.warning(f"Login failed - user not found", email=login_data.email)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                    headers={"WWW-Authenticate": "Bearer"}
                )

            # Verify password
            if not verify_password(login_data.password, user.hashed_password):
                logger.warning(f"Login failed - invalid password", email=login_data.email)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                    headers={"WWW-Authenticate": "Bearer"}
                )

            # Check if user is active
            if not user.is_active:
                logger.warning(f"Login failed - user not active", email=login_data.email)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is deactivated"
                )

            # Generate tokens
            access_token = create_access_token(user.id, user.email)
            refresh_token = create_refresh_token(user.id, user.email)

            logger.info(f"User authenticated successfully", user_id=str(user.id), email=user.email)

            return Token(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Authentication failed",
                email=login_data.email,
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed"
            )

    async def refresh_access_token(
        self,
        db: AsyncSession,
        refresh_token: str
    ) -> Token:
        """
        Generate new access and refresh tokens using a refresh token.

        Args:
            db: Database session
            refresh_token: JWT refresh token

        Returns:
            Token object with new access and refresh tokens

        Raises:
            HTTPException: If token is invalid or user not found
        """
        try:
            # Verify refresh token
            token_data = verify_token(refresh_token, expected_type="refresh")

            if not token_data.user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                    headers={"WWW-Authenticate": "Bearer"}
                )

            # Get user from database
            user = await db_service.get_user_by_id(db, token_data.user_id)

            if not user:
                logger.warning(f"Token refresh failed - user not found", user_id=str(token_data.user_id))
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"}
                )

            # Check if user is active
            if not user.is_active:
                logger.warning(f"Token refresh failed - user not active", user_id=str(user.id))
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is deactivated"
                )

            # Generate new tokens
            new_access_token = create_access_token(user.id, user.email)
            new_refresh_token = create_refresh_token(user.id, user.email)

            logger.info(f"Access token refreshed successfully", user_id=str(user.id))

            return Token(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                token_type="bearer"
            )

        except JWTError as e:
            logger.warning(f"Token refresh failed - invalid token", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Token refresh failed",
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token refresh failed"
            )


# Global auth service instance
auth_service = AuthService()
