"""
JWT token utilities for authentication.
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID
from jose import JWTError, jwt
from app.config import settings
from app.schemas.auth import TokenData


def create_access_token(user_id: UUID, email: str) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: User's UUID
        email: User's email address

    Returns:
        Encoded JWT token string
    """
    expires_delta = timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    expire = datetime.now(timezone.utc) + expires_delta

    to_encode = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "type": "access"
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def create_refresh_token(user_id: UUID, email: str) -> str:
    """
    Create a JWT refresh token.

    Args:
        user_id: User's UUID
        email: User's email address

    Returns:
        Encoded JWT refresh token string
    """
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    expire = datetime.now(timezone.utc) + expires_delta

    to_encode = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "type": "refresh"
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def verify_token(token: str, expected_type: str = "access") -> TokenData:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string to verify
        expected_type: Expected token type ("access" or "refresh")

    Returns:
        TokenData object with decoded token information

    Raises:
        JWTError: If token is invalid, expired, or type doesn't match
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        user_id_str: str | None = payload.get("sub")
        email: str | None = payload.get("email")
        token_type: str = payload.get("type", "access")

        if user_id_str is None or email is None:
            raise JWTError("Invalid token payload")

        if token_type != expected_type:
            raise JWTError(f"Invalid token type: expected {expected_type}, got {token_type}")

        return TokenData(
            user_id=UUID(user_id_str),
            email=email,
            token_type=token_type
        )

    except JWTError as e:
        raise JWTError(f"Token verification failed: {str(e)}")
