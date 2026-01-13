"""Tests for authentication routes and service."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.user import (
    Token,
    UserCreate,
    UserResponse,
    UserRole,
)
from src.services.auth_service import AuthService


class TestAuthService:
    """Tests for AuthService."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password123"
        hashed = AuthService.hash_password(password)

        # Hash should be different from original
        assert hashed != password
        # Hash should be verifiable
        assert AuthService.verify_password(password, hashed)

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "correct_password"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "correct_password"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password("wrong_password", hashed) is False

    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "user-123", "email": "test@example.com", "role": "user"}
        token = AuthService.create_access_token(data)

        # Token should be a string
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        """Test access token with custom expiry."""
        data = {"sub": "user-123", "email": "test@example.com"}
        expires = timedelta(hours=2)

        token = AuthService.create_access_token(data, expires_delta=expires)
        assert isinstance(token, str)

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = "user-123"
        token = AuthService.create_refresh_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        data = {"sub": "user-123", "email": "test@example.com", "role": "user"}
        token = AuthService.create_access_token(data)

        payload = AuthService.decode_token(token)

        assert payload is not None
        assert payload.sub == "user-123"
        assert payload.email == "test@example.com"
        assert payload.role == UserRole.USER

    def test_decode_invalid_token(self):
        """Test decoding an invalid token."""
        invalid_token = "invalid.token.here"

        payload = AuthService.decode_token(invalid_token)

        assert payload is None

    def test_decode_expired_token(self):
        """Test decoding an expired token."""
        data = {"sub": "user-123", "email": "test@example.com", "role": "user"}
        # Create token with negative expiry (already expired)
        expires = timedelta(seconds=-10)
        token = AuthService.create_access_token(data, expires_delta=expires)

        payload = AuthService.decode_token(token)

        assert payload is None


class TestAuthServiceAsync:
    """Async tests for AuthService."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def auth_service(self, mock_session):
        """Create auth service with mock session."""
        return AuthService(mock_session)

    @pytest.fixture
    def sample_user_db(self):
        """Create sample user database record."""
        user = MagicMock()
        user.id = "user-123"
        user.email = "test@example.com"
        user.full_name = "Test User"
        user.hashed_password = AuthService.hash_password("password123")
        user.is_active = True
        user.is_superuser = False
        user.created_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        return user

    @pytest.mark.asyncio
    async def test_get_user_by_email_found(self, auth_service, mock_session, sample_user_db):
        """Test getting user by email when found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user_db
        mock_session.execute.return_value = mock_result

        user = await auth_service.get_user_by_email("test@example.com")

        assert user is not None
        assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, auth_service, mock_session):
        """Test getting user by email when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        user = await auth_service.get_user_by_email("nonexistent@example.com")

        assert user is None

    @pytest.mark.asyncio
    async def test_create_user(self, auth_service, mock_session):
        """Test creating a new user."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        user_data = UserCreate(
            email="new@example.com",
            password="password123",
            full_name="New User",
        )

        await auth_service.create_user(user_data)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_email_exists(self, auth_service, mock_session, sample_user_db):
        """Test creating user with existing email."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user_db
        mock_session.execute.return_value = mock_result

        user_data = UserCreate(
            email="test@example.com",  # Existing email
            password="password123",
            full_name="New User",
        )

        with pytest.raises(ValueError, match="Email already registered"):
            await auth_service.create_user(user_data)

    @pytest.mark.asyncio
    async def test_authenticate_success(self, auth_service, mock_session, sample_user_db):
        """Test successful authentication."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user_db
        mock_session.execute.return_value = mock_result

        user = await auth_service.authenticate("test@example.com", "password123")

        assert user is not None
        assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_authenticate_wrong_password(self, auth_service, mock_session, sample_user_db):
        """Test authentication with wrong password."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user_db
        mock_session.execute.return_value = mock_result

        user = await auth_service.authenticate("test@example.com", "wrong_password")

        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, auth_service, mock_session):
        """Test authentication when user not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        user = await auth_service.authenticate("nonexistent@example.com", "password123")

        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self, auth_service, mock_session, sample_user_db):
        """Test authentication for inactive user."""
        sample_user_db.is_active = False
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user_db
        mock_session.execute.return_value = mock_result

        user = await auth_service.authenticate("test@example.com", "password123")

        assert user is None

    @pytest.mark.asyncio
    async def test_create_tokens(self, auth_service, sample_user_db):
        """Test creating access and refresh tokens."""
        tokens = await auth_service.create_tokens(sample_user_db)

        assert isinstance(tokens, Token)
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"
        assert tokens.expires_in > 0

    def test_to_response(self, sample_user_db):
        """Test converting user DB to response model."""
        response = AuthService.to_response(sample_user_db)

        assert isinstance(response, UserResponse)
        assert response.id == sample_user_db.id
        assert response.email == sample_user_db.email
        assert response.full_name == sample_user_db.full_name
        assert response.is_active == sample_user_db.is_active


class TestPasswordValidation:
    """Tests for password validation."""

    def test_password_min_length(self):
        """Test password minimum length validation."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="short",  # Less than 8 characters
                full_name="Test",
            )

    def test_password_valid_length(self):
        """Test valid password length."""
        user = UserCreate(
            email="test@example.com",
            password="validpassword123",
            full_name="Test",
        )
        assert len(user.password) >= 8


class TestEmailValidation:
    """Tests for email validation."""

    def test_invalid_email(self):
        """Test invalid email format."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            UserCreate(
                email="invalid-email",
                password="password123",
                full_name="Test",
            )

    def test_valid_email(self):
        """Test valid email format."""
        user = UserCreate(
            email="valid@example.com",
            password="password123",
            full_name="Test",
        )
        assert "@" in user.email
