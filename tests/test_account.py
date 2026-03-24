"""
Account Service Tests
Based on actual code: src/services/account_service.py
"""
import pytest
from src.services.account_service import (
    AccountService, UserRole, LoginResult,
    User, LoginLog
)


class TestAccountService:
    @pytest.fixture
    def account_service(self):
        return AccountService()
    
    def test_can_be_instantiated(self, account_service):
        assert account_service is not None
    
    def test_has_authenticate_method(self, account_service):
        assert hasattr(account_service, 'authenticate')


class TestAccountEnums:
    def test_user_role_enum(self):
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.USER.value == "user"
        assert UserRole.GUEST.value == "guest"
    
    def test_login_result_enum(self):
        assert LoginResult.SUCCESS.value == "success"
        assert LoginResult.INVALID_PASSWORD.value == "invalid_password"


class TestUser:
    def test_can_create_user(self):
        user = User(
            id="user_1",
            username="testuser",
            password_hash="hash123"
        )
        assert user.username == "testuser"
        assert user.role == UserRole.USER
