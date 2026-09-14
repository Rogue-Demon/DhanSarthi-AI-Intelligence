"""
API integration tests for /api/v1/creditworthiness endpoints.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    """TestClient that overrides DB dependency."""
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, dict[str, str]]:
    """Register and login User A and User B, returning their Authorization headers."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "dcs_user_a@test.com", "password": "password123"},
    )
    login_a = client.post(
        "/api/v1/auth/login",
        json={"email": "dcs_user_a@test.com", "password": "password123"},
    )
    token_a = login_a.json()["access_token"]

    client.post(
        "/api/v1/auth/register",
        json={"email": "dcs_user_b@test.com", "password": "password123"},
    )
    login_b = client.post(
        "/api/v1/auth/login",
        json={"email": "dcs_user_b@test.com", "password": "password123"},
    )
    token_b = login_b.json()["access_token"]

    return {
        "user_a": {"Authorization": f"Bearer {token_a}"},
        "user_b": {"Authorization": f"Bearer {token_b}"},
    }


def test_get_creditworthiness_endpoint(client: TestClient, auth_headers: dict):
    """Test GET /api/v1/creditworthiness returns valid DCS assessment structure."""
    response = client.get("/api/v1/creditworthiness", headers=auth_headers["user_a"])
    assert response.status_code == 200
    data = response.json()

    assert "creditworthiness_score" in data
    assert data["score_scale"] == "0-100"
    assert "status" in data
    assert "risk_band" in data
    assert "loan_readiness" in data
    assert "data_coverage" in data
    assert "disclaimer" in data
    assert "is not a CIBIL score" in data["disclaimer"]


def test_recalculate_creditworthiness_endpoint(client: TestClient, auth_headers: dict):
    """Test POST /api/v1/creditworthiness/recalculate triggers on-demand evaluation."""
    # Seed 3 months of income for User A
    for m in ("06", "07", "08"):
        client.post(
            "/api/v1/income",
            json={"amount": "100000.00", "source": "API Test Salary", "category": "Salary", "income_date": f"2026-{m}-01"},
            headers=auth_headers["user_a"],
        )
        client.post(
            "/api/v1/expenses",
            json={"amount": "30000.00", "description": "API Test Expense", "category": "Food", "expense_date": f"2026-{m}-02"},
            headers=auth_headers["user_a"],
        )

    recalc_resp = client.post("/api/v1/creditworthiness/recalculate", headers=auth_headers["user_a"])
    assert recalc_resp.status_code == 200
    data = recalc_resp.json()

    assert data["status"] == "CALCULATED"
    assert data["creditworthiness_score"] is not None
    assert 0 <= data["creditworthiness_score"] <= 100


def test_creditworthiness_history_endpoint(client: TestClient, auth_headers: dict):
    """Test GET /api/v1/creditworthiness/history returns snapshots list."""
    client.post("/api/v1/creditworthiness/recalculate", headers=auth_headers["user_a"])

    resp = client.get("/api/v1/creditworthiness/history", headers=auth_headers["user_a"])
    assert resp.status_code == 200
    data = resp.json()

    assert "history" in data
    assert isinstance(data["history"], list)
    if len(data["history"]) > 0:
        assert "snapshot_date" in data["history"][0]
        assert "confidence_score" in data["history"][0]


def test_share_consent_endpoint(client: TestClient, auth_headers: dict):
    """Test POST /api/v1/creditworthiness/share-consent records user consent."""
    req_body = {"recipient_name": "HDFC Bank Financial Services"}
    resp = client.post("/api/v1/creditworthiness/share-consent", json=req_body, headers=auth_headers["user_a"])
    assert resp.status_code == 200
    data = resp.json()

    assert data["recipient_name"] == "HDFC Bank Financial Services"
    assert data["consent_granted"] is True
    assert "HDFC Bank Financial Services" in data["message"]


def test_creditworthiness_user_isolation_api(client: TestClient, auth_headers: dict):
    """Test User A and User B profiles are strictly isolated."""
    # Seed data for User A
    for m in ("06", "07", "08"):
        client.post(
            "/api/v1/income",
            json={"amount": "150000.00", "source": "User A Salary", "category": "Salary", "income_date": f"2026-{m}-01"},
            headers=auth_headers["user_a"],
        )

    # Recalculate for User A
    resp_a = client.post("/api/v1/creditworthiness/recalculate", headers=auth_headers["user_a"])
    assert resp_a.status_code == 200
    data_a = resp_a.json()

    # Get profile for User B (has no records)
    resp_b = client.get("/api/v1/creditworthiness", headers=auth_headers["user_b"])
    assert resp_b.status_code == 200
    data_b = resp_b.json()

    assert data_a["status"] == "CALCULATED"
    assert data_a["creditworthiness_score"] is not None

    assert data_b["status"] == "INSUFFICIENT_DATA"
    assert data_b["creditworthiness_score"] is None
