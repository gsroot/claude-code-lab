"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.models.user import (
    ChangePassword,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
)
from src.services.auth_service import AuthService

router = APIRouter()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> UserResponse:
    """Get current authenticated user.

    Args:
        credentials: Bearer token credentials
        db: Database session

    Returns:
        Current user

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    auth_service = AuthService(db)

    # Decode token
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user
    user = await auth_service.get_user_by_id(payload.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return auth_service.to_response(user)


async def get_current_active_user(
    current_user: UserResponse = Depends(get_current_user),  # noqa: B008
) -> UserResponse:
    """Get current active user (alias for get_current_user)."""
    return current_user


@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    """Register a new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Created user
    """
    auth_service = AuthService(db)

    try:
        user = await auth_service.create_user(user_data)
        await db.commit()
        logger.info(f"New user registered: {user.email}")
        return auth_service.to_response(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/auth/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    """Login and get access token.

    Args:
        login_data: Login credentials
        db: Database session

    Returns:
        Access and refresh tokens
    """
    auth_service = AuthService(db)

    user = await auth_service.authenticate(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tokens = await auth_service.create_tokens(user)
    logger.info(f"User logged in: {user.email}")
    return tokens


@router.post("/auth/refresh", response_model=Token)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    """Refresh access token using refresh token.

    Args:
        credentials: Bearer token (refresh token)
        db: Database session

    Returns:
        New access and refresh tokens
    """
    token = credentials.credentials
    auth_service = AuthService(db)

    # Decode refresh token
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user
    user = await auth_service.get_user_by_id(payload.sub)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
        )

    # Create new tokens
    tokens = await auth_service.create_tokens(user)
    return tokens


@router.get("/auth/me", response_model=UserResponse)
async def get_me(
    current_user: UserResponse = Depends(get_current_user),  # noqa: B008
):
    """Get current user profile.

    Args:
        current_user: Current authenticated user

    Returns:
        User profile
    """
    return current_user


@router.post("/auth/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: UserResponse = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    """Change current user's password.

    Args:
        password_data: Password change data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message
    """
    auth_service = AuthService(db)

    try:
        await auth_service.update_password(
            user_id=current_user.id,
            current_password=password_data.current_password,
            new_password=password_data.new_password,
        )
        await db.commit()
        return {"message": "Password updated successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/auth/logout")
async def logout(
    current_user: UserResponse = Depends(get_current_user),  # noqa: B008
):
    """Logout current user.

    Note: JWT tokens are stateless, so this endpoint is mainly
    for client-side token cleanup. For true logout, implement
    a token blacklist using Redis.

    Args:
        current_user: Current authenticated user

    Returns:
        Success message
    """
    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Successfully logged out"}
