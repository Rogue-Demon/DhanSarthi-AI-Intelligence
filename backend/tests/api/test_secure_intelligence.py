"""Tests for Secure Financial Intelligence API endpoints and service logic."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.models.user import User
from app.models.profile import Profile
from app.services.secure_financial_intelligence_service import SecureFinancialIntelligenceService


@pytest.fixture
def client(db_session: Session) -> TestClient:
    """Provide a TestClient with DB session override."""
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create or retrieve a user and profile for secure intelligence testing."""
    from app.core.security import hash_password
    user = db_session.query(User).filter(User.email == "secure_test@example.com").first()
    if not user:
        user = User(email="secure_test@example.com", password_hash=hash_password("password123"))
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    profile = db_session.query(Profile).filter(Profile.user_id == user.id).first()
    if not profile:
        from app.models.enums import Persona
        profile = Profile(
            user_id=user.id,
            display_name="Test Secure User",
            persona=Persona.PROFESSIONAL,
            country="IN",
            currency="INR",
        )
        db_session.add(profile)
        db_session.commit()
    return user




class TestSecureFinancialIntelligence:
    def test_validate_invalid_token(self, client: TestClient):
        res = client.post("/api/v1/secure-fi/validate", json={"token": "nonexistent_token_1234567890"})
        assert res.status_code == 200
        data = res.json()
        assert data["valid"] is False
        assert data["requires_pin"] is False

    def test_validate_valid_token(self, client: TestClient, db_session: Session, test_user: User):
        svc = SecureFinancialIntelligenceService(db_session)
        token_record = svc.create_token(user_id=test_user.id, pin="1234")

        res = client.post("/api/v1/secure-fi/validate", json={"token": token_record.token})
        assert res.status_code == 200
        data = res.json()
        assert data["valid"] is True
        assert data["requires_pin"] is True

    def test_authenticate_correct_pin(self, client: TestClient, db_session: Session, test_user: User):
        svc = SecureFinancialIntelligenceService(db_session)
        token_record = svc.create_token(user_id=test_user.id, pin="4321")

        res = client.post("/api/v1/secure-fi/authenticate", json={"token": token_record.token, "pin": "4321"})
        assert res.status_code == 200
        data = res.json()
        assert data["authenticated"] is True
        assert "session_token" in data
        assert data["session_token"] is not None

    def test_authenticate_incorrect_pin(self, client: TestClient, db_session: Session, test_user: User):
        svc = SecureFinancialIntelligenceService(db_session)
        token_record = svc.create_token(user_id=test_user.id, pin="9999")

        res = client.post("/api/v1/secure-fi/authenticate", json={"token": token_record.token, "pin": "0000"})
        assert res.status_code == 401
        assert "Incorrect PIN" in res.json()["detail"]

    def test_lockout_after_failed_attempts(self, client: TestClient, db_session: Session, test_user: User):
        svc = SecureFinancialIntelligenceService(db_session)
        token_record = svc.create_token(user_id=test_user.id, pin="1111")

        # 5 failed attempts
        for _ in range(5):
            client.post("/api/v1/secure-fi/authenticate", json={"token": token_record.token, "pin": "0000"})

        # 6th attempt should return 429 Too Many Requests
        res = client.post("/api/v1/secure-fi/authenticate", json={"token": token_record.token, "pin": "1111"})
        assert res.status_code == 429
        assert "Too many failed attempts" in res.json()["detail"]

    def test_get_intelligence_success(self, client: TestClient, db_session: Session, test_user: User):
        svc = SecureFinancialIntelligenceService(db_session)
        token_record = svc.create_token(user_id=test_user.id, pin="5555")

        auth_res = client.post("/api/v1/secure-fi/authenticate", json={"token": token_record.token, "pin": "5555"})
        session_token = auth_res.json()["session_token"]

        intel_res = client.get("/api/v1/secure-fi/intelligence", headers={"X-Secure-Session": session_token})
        assert intel_res.status_code == 200
        data = intel_res.json()

        assert data["profile"]["name"] == "Test Secure User"
        assert data["profile"]["email"] == "secure_test@example.com"
        assert "financial_snapshot" in data
        assert "risks" in data
        assert "opportunities" in data
        assert "ai_advice" in data
        assert data["read_only"] is True

    def test_get_intelligence_without_session(self, client: TestClient):
        res = client.get("/api/v1/secure-fi/intelligence")
        assert res.status_code == 422  # Header missing validation error
