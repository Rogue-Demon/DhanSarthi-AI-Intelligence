"""
Automated Tests for DCS Integration, Staleness, Snapshot Comparisons, User Isolation, and Document Intelligence Pipeline.
"""

from datetime import date, datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.models.user import User
from app.models.income import Income
from app.models.expense import Expense
from app.models.financial_document import FinancialDocument, DocumentStatus
from app.models.enums import DocumentType
from app.models.creditworthiness import CreditProfile, CreditScoreSnapshot, CreditStatus, RiskBand
from app.services.creditworthiness_service import CreditworthinessService


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
        json={"email": "dcs_integ_a@test.com", "password": "password123"},
    )
    login_a = client.post(
        "/api/v1/auth/login",
        json={"email": "dcs_integ_a@test.com", "password": "password123"},
    )
    token_a = login_a.json()["access_token"]

    client.post(
        "/api/v1/auth/register",
        json={"email": "dcs_integ_b@test.com", "password": "password123"},
    )
    login_b = client.post(
        "/api/v1/auth/login",
        json={"email": "dcs_integ_b@test.com", "password": "password123"},
    )
    token_b = login_b.json()["access_token"]

    return {
        "user_a": {"Authorization": f"Bearer {token_a}"},
        "user_b": {"Authorization": f"Bearer {token_b}"},
    }


def test_dcs_summary_endpoint(client: TestClient, auth_headers: dict):
    """Verify GET /api/v1/creditworthiness/summary returns concise summary payload."""
    response = client.get("/api/v1/creditworthiness/summary", headers=auth_headers["user_a"])
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "status" in data
    assert "score_status" in data
    assert "disclaimer" in data
    assert "cibil" in data["disclaimer"].lower()


def test_dcs_score_comparison(db_session: Session):
    """Verify DCS snapshot comparison calculates accurate score deltas."""
    user = User(email="snap_test@example.com", password_hash="hashed_pw")
    db_session.add(user)
    db_session.commit()

    service = CreditworthinessService(db_session)

    # Create two snapshots
    snap1 = CreditScoreSnapshot(
        user_id=user.id,
        snapshot_date=date(2026, 8, 1),
        score=68,
        status=CreditStatus.CALCULATED,
        risk_band=RiskBand.GOOD,
        loan_readiness="NEARLY_READY",
        confidence_score=0.75,
        dimension_scores={"cash_flow_health": {"weighted_score": 14.0}},
    )
    snap2 = CreditScoreSnapshot(
        user_id=user.id,
        snapshot_date=date(2026, 9, 1),
        score=74,
        status=CreditStatus.CALCULATED,
        risk_band=RiskBand.GOOD,
        loan_readiness="READY",
        confidence_score=0.85,
        dimension_scores={"cash_flow_health": {"weighted_score": 20.0}},
    )
    db_session.add_all([snap1, snap2])
    db_session.commit()

    comp = service.get_score_comparison(user.id)
    assert comp["has_comparison"] is True
    assert comp["previous_score"] == 68
    assert comp["current_score"] == 74
    assert comp["score_delta"] == 6
    assert "improved by 6 points" in comp["explanation_summary"]


def test_dcs_action_recommendations(db_session: Session):
    """Verify action recommendations are generated deterministically based on financial weak spots."""
    user = User(email="recs_test@example.com", password_hash="hashed_pw")
    db_session.add(user)
    db_session.commit()

    service = CreditworthinessService(db_session)

    profile = CreditProfile(
        user_id=user.id,
        status=CreditStatus.CALCULATED,
        risk_band=RiskBand.MODERATE,
        months_available=4,
        dti_ratio=0.55,
        dimension_scores={
            "cash_flow_health": {"score": 40.0},
            "budget_discipline": {"status": "NOT_CONFIGURED"},
        }
    )
    db_session.add(profile)
    db_session.commit()

    recs = service.get_action_recommendations(profile)
    assert len(recs) > 0
    assert any("debt" in r.lower() for r in recs)
    assert any("budget" in r.lower() for r in recs)


def test_dcs_user_isolation(client: TestClient, auth_headers: dict):
    """Verify User A cannot access User B's creditworthiness data."""
    # User A seeds data
    for m in ("06", "07", "08"):
        client.post(
            "/api/v1/income",
            json={"amount": "120000.00", "source": "User A Salary", "category": "Salary", "income_date": f"2026-{m}-01"},
            headers=auth_headers["user_a"],
        )

    # Recalculate User A
    client.post("/api/v1/creditworthiness/recalculate", headers=auth_headers["user_a"])

    # User B queries their profile
    res_b = client.get("/api/v1/creditworthiness", headers=auth_headers["user_b"])
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["status"] == "INSUFFICIENT_DATA"
    assert data_b["creditworthiness_score"] is None


def test_document_confirmation_dcs_eligibility_flow(db_session: Session):
    """
    Verify Document Intelligence pipeline boundary:
    Upload/OCR alone does NOT grant document evidence to DCS until document status is CONFIRMED or EXTRACTED.
    """
    user = User(email="doc_dcs@example.com", password_hash="hashed_pw")
    db_session.add(user)
    db_session.commit()

    # 1. Unconfirmed / UNKNOWN document
    doc_unconfirmed = FinancialDocument(
        user_id=user.id,
        original_filename="draft_slip.pdf",
        storage_key="test_storage_key_draft",
        mime_type="application/pdf",
        file_size=1024,
        checksum="test_checksum_draft",
        document_type=DocumentType.UNKNOWN,
        status=DocumentStatus.UPLOADED,
    )
    db_session.add(doc_unconfirmed)
    db_session.commit()

    service = CreditworthinessService(db_session)
    profile1 = service.calculate_and_save_profile(user.id)
    assert profile1.data_coverage.get("document_evidence_available") is False

    # 2. Confirmed salary slip document -> DCS recognizes document evidence
    doc_confirmed = FinancialDocument(
        user_id=user.id,
        original_filename="salary_slip_august.pdf",
        storage_key="test_storage_key_salary",
        mime_type="application/pdf",
        file_size=2048,
        checksum="test_checksum_salary",
        document_type=DocumentType.SALARY_SLIP,
        status=DocumentStatus.CONFIRMED,
    )
    db_session.add(doc_confirmed)
    db_session.commit()

    profile2 = service.calculate_and_save_profile(user.id)
    assert profile2.data_coverage.get("document_evidence_available") is True
