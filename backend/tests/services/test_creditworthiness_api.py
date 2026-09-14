
"""
API tests for DhanSarthi Creditworthiness Score (DCS) endpoints.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.profile import Profile
from app.models.enums import Persona, RiskProfile
from app.models.income import Income


@pytest.fixture
def test_user(db_session: Session) -> User:
    u = db_session.query(User).filter(User.id == 9901).first()
    if not u:
        u = User(id=9901, email="dcs_api_user@test.com", password_hash="hash")
        db_session.add(u)
        db_session.add(
            Profile(
                user_id=9901,
                display_name="DCS API User",
                persona=Persona.PROFESSIONAL,
                country="IN",
                currency="INR",
                risk_profile=RiskProfile.MODERATE,
            )
        )
        db_session.commit()
    return u


@pytest.fixture
def client(db_session: Session, test_user: User) -> TestClient:
    def _override_get_db():
        yield db_session

    def _override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    
    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_get_creditworthiness_uncalculated(client: TestClient):
    response = client.get("/api/v1/creditworthiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "INSUFFICIENT_DATA"
    assert data["creditworthiness_score"] is None
    assert "disclaimer" in data


def test_recalculate_creditworthiness(client: TestClient, db_session: Session, test_user: User):
    # Add 3 months of income for user
    for m in range(1, 4):
        db_session.add(
            Income(
                user_id=test_user.id,
                source="Monthly Salary",
                amount=Decimal("150000.00"),
                category="Salary",
                income_date=datetime.date(2026, m, 15),
            )
        )
    db_session.commit()

    response = client.post("/api/v1/creditworthiness/recalculate")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CALCULATED"
    assert data["creditworthiness_score"] is not None
    assert data["creditworthiness_score"] > 0


def test_share_consent_workflow(client: TestClient):
    payload = {
        "recipient_name": "Axis Bank Loan Portal",
    }
    response = client.post("/api/v1/creditworthiness/share-consent", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["consent_granted"] is True
    assert data["recipient_name"] == "Axis Bank Loan Portal"
