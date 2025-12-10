"""Authentication service with JWT handling."""

from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from loguru import logger
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import UserDB
from src.models.user import (
    Token,
    TokenPayload,
    UserCreate,
    UserResponse,
    UserRole,
)
from src.utils.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for authentication operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password

        Returns:
            True if password matches
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a JWT access token.

        Args:
            data: Token payload data
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.access_token_expire_minutes
            )

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
        })

        return jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create a refresh token.

        Args:
            user_id: User ID

        Returns:
            Encoded refresh token
        """
        expire = datetime.utcnow() + timedelta(days=7)

        return jwt.encode(
            {"sub": user_id, "exp": expire, "type": "refresh"},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

    @staticmethod
    def decode_token(token: str) -> TokenPayload | None:
        """Decode and validate a JWT token.

        Args:
            token: JWT token string

        Returns:
            Token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )

            return TokenPayload(
                sub=payload["sub"],
                email=payload.get("email", ""),
                role=UserRole(payload.get("role", "user")),
                exp=datetime.fromtimestamp(payload["exp"]),
                iat=datetime.fromtimestamp(payload["iat"]),
            )
        except JWTError as e:
            logger.warning(f"JWT decode error: {e}")
            return None

    async def get_user_by_email(self, email: str) -> UserDB | None:
        """Get user by email.

        Args:
            email: User email

        Returns:
            User record or None
        """
        result = await self.session.execute(
            select(UserDB).where(UserDB.email == email)
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> UserDB | None:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User record or None
        """
        result = await self.session.execute(
            select(UserDB).where(UserDB.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_user(self, user_data: UserCreate) -> UserDB:
        """Create a new user.

        Args:
            user_data: User registration data

        Returns:
            Created user record

        Raises:
            ValueError: If email already exists
        """
        # Check if email already exists
        existing = await self.get_user_by_email(user_data.email)
        if existing:
            raise ValueError("Email already registered")

        # Create user
        user = UserDB(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=self.hash_password(user_data.password),
        )

        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)

        logger.info(f"Created user: {user.email}")
        return user

    async def authenticate(self, email: str, password: str) -> UserDB | None:
        """Authenticate a user.

        Args:
            email: User email
            password: Plain text password

        Returns:
            User record if authenticated, None otherwise
        """
        user = await self.get_user_by_email(email)

        if not user:
            return None

        if not self.verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        return user

    async def create_tokens(self, user: UserDB) -> Token:
        """Create access and refresh tokens for a user.

        Args:
            user: User record

        Returns:
            Token response with access and refresh tokens
        """
        access_token = self.create_access_token(
            data={
                "sub": user.id,
                "email": user.email,
                "role": "admin" if user.is_superuser else "user",
            }
        )

        refresh_token = self.create_refresh_token(user.id)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def update_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> bool:
        """Update user password.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            True if updated successfully

        Raises:
            ValueError: If current password is incorrect
        """
        user = await self.get_user_by_id(user_id)

        if not user:
            raise ValueError("User not found")

        if not self.verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")

        user.hashed_password = self.hash_password(new_password)
        await self.session.flush()

        logger.info(f"Password updated for user: {user.email}")
        return True

    @staticmethod
    def to_response(user: UserDB) -> UserResponse:
        """Convert user DB model to response model.

        Args:
            user: User database record

        Returns:
            User response model
        """
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            role=UserRole.ADMIN if user.is_superuser else UserRole.USER,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
