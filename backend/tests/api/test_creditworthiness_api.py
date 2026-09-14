"""
API integration tests for /api/v1/creditworthiness endpoints.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient


def test_get_creditworthiness_endpoint(client: TestClient, auth_headers: dict):
    """Test GET /api/v1/creditworthiness returns valid DCS assessment structure."""
    response = client.get("/api/v1/creditworthiness", headers=auth_headers["user_a"])
    assert response.status_code == 200
    data = response.json()

    assert "creditworthiness_score" in data
    assert "status" in data
    assert "risk_band" in data
    assert "loan_readiness" in data
    assert "data_coverage" in data
    assert "disclaimer" in data
    assert "NOT an official credit bureau score" in data["disclaimer"]


def test_recalculate_creditworthiness_endpoint(client: TestClient, auth_headers: dict):
    """Test POST /api/v1/creditworthiness/recalculate triggers on-demand evaluation."""
    # Seed income for User A
    client.post(
        "/api/v1/income",
        json={"amount": "100000.00", "source": "API Test Salary", "category": "Salary", "income_date": "2026-09-01"},
        headers=auth_headers["user_a"],
    )
    client.post(
        "/api/v1/expenses",
        json={"amount": "30000.00", "description": "API Test Expense", "category": "Food", "expense_date": "2026-09-02"},
        headers=auth_headers["user_a"],
    )

    recalc_resp = client.post("/api/v1/creditworthiness/recalculate", headers=auth_headers["user_a"])
    assert recalc_resp.status_code == 200
    data = recalc_resp.json()

    assert data["status"] in ("CALCULATED", "INSUFFICIENT_DATA")


def test_creditworthiness_history_endpoint(client: TestClient, auth_headers: dict):
    """Test GET /api/v1/creditworthiness/history returns snapshots list."""
    # Trigger recalculation first to record a snapshot
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
