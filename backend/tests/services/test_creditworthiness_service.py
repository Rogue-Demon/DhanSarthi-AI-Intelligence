"""
Unit tests for DhanSarthi Creditworthiness Score (DCS) Engine.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.profile import Profile
from app.models.enums import Persona, RiskProfile, LoanType, AssetType
from app.models.income import Income
from app.models.expense import Expense
from app.models.loan import Loan, LoanStatus
from app.models.asset import Asset
from app.models.budget import Budget
from app.models.creditworthiness import (
    CreditStatus,
    RiskBand,
    LoanReadinessState,
    CreditConfidenceLevel,
)
from app.services.creditworthiness_service import CreditworthinessService


def _seed_test_user(db: Session, user_id: int) -> User:
    u = User(id=user_id, email=f"dcs_user_{user_id}@test.com", password_hash="hash")
    db.add(u)
    db.add(
        Profile(
            user_id=user_id,
            display_name=f"DCS User {user_id}",
            persona=Persona.PROFESSIONAL,
            country="IN",
            currency="INR",
            risk_profile=RiskProfile.MODERATE,
        )
    )
    db.flush()
    return u


def test_creditworthiness_insufficient_data(db_session: Session):
    """Test user with zero/insufficient financial history yields INSUFFICIENT_DATA."""
    user = _seed_test_user(db_session, 8801)
    service = CreditworthinessService(db_session)

    profile = service.calculate_and_save_profile(user.id)

    assert profile.status == CreditStatus.INSUFFICIENT_DATA
    assert profile.creditworthiness_score is None
    assert profile.risk_band == RiskBand.INSUFFICIENT
    assert profile.loan_readiness == LoanReadinessState.INSUFFICIENT_DATA
    assert profile.confidence_score == 0.0
    assert profile.confidence_label == CreditConfidenceLevel.LOW


def test_creditworthiness_healthy_financial_profile(db_session: Session):
    """Test user with 6+ months stable income, low DTI, and high savings yields strong score."""
    user = _seed_test_user(db_session, 8802)

    # Seed 6 months of stable income
    for month in range(1, 7):
        db_session.add(
            Income(
                user_id=user.id,
                source="Tech Corp Salary",
                amount=Decimal("120000.00"),
                category="Salary",
                income_date=datetime.date(2026, month, 15),
            )
        )
        db_session.add(
            Expense(
                user_id=user.id,
                description="Rent & Groceries",
                amount=Decimal("40000.00"),
                category="Housing",
                expense_date=datetime.date(2026, month, 18),
            )
        )

    # Seed low loan EMI
    db_session.add(
        Loan(
            user_id=user.id,
            loan_type=LoanType.VEHICLE,
            lender="HDFC",
            principal_amount=Decimal("500000.00"),
            outstanding_amount=Decimal("200000.00"),
            interest_rate=Decimal("0.085"),
            tenure=60,
            emi=Decimal("12000.00"),
            start_date=datetime.date(2025, 1, 1),
            status=LoanStatus.ACTIVE,
        )
    )

    # Seed liquid asset reserve
    db_session.add(
        Asset(
            user_id=user.id,
            name="Bank Savings Account",
            asset_type=AssetType.CASH,
            value=Decimal("400000.00"),
            valuation_date=datetime.date.today(),
        )
    )

    db_session.commit()

    service = CreditworthinessService(db_session)
    profile = service.calculate_and_save_profile(user.id)

    assert profile.status == CreditStatus.CALCULATED
    assert profile.creditworthiness_score is not None
    assert profile.creditworthiness_score >= 75
    assert profile.risk_band in (RiskBand.STRONG, RiskBand.GOOD)
    assert profile.loan_readiness == LoanReadinessState.READY
    assert profile.confidence_label == CreditConfidenceLevel.HIGH
    assert profile.months_available == 6
    assert len(profile.positive_factors) > 0


def test_creditworthiness_defaulted_loan_penalty(db_session: Session):
    """Test user with defaulted loan receives lower score and HIGH_RISK loan readiness."""
    user = _seed_test_user(db_session, 8803)

    # Seed income & expenses
    for month in range(1, 4):
        db_session.add(
            Income(
                user_id=user.id,
                source="Freelance Income",
                amount=Decimal("60000.00"),
                category="Freelance",
                income_date=datetime.date(2026, month, 10),
            )
        )
        db_session.add(
            Expense(
                user_id=user.id,
                description="Living Cost",
                amount=Decimal("45000.00"),
                category="Living",
                expense_date=datetime.date(2026, month, 12),
            )
        )

    # Seed defaulted loan
    db_session.add(
        Loan(
            user_id=user.id,
            loan_type=LoanType.PERSONAL,
            lender="NBFC",
            principal_amount=Decimal("150000.00"),
            outstanding_amount=Decimal("150000.00"),
            interest_rate=Decimal("0.18"),
            tenure=24,
            emi=Decimal("45000.00"),
            start_date=datetime.date(2025, 1, 1),
            status=LoanStatus.DEFAULTED,
        )
    )

    db_session.commit()

    service = CreditworthinessService(db_session)
    profile = service.calculate_and_save_profile(user.id)

    assert profile.status == CreditStatus.CALCULATED
    assert profile.loan_readiness == LoanReadinessState.HIGH_RISK
    assert any("default" in rf.lower() for rf in profile.risk_factors)


def test_user_isolation_creditworthiness(db_session: Session):
    """Verify User A data never influences User B creditworthiness score."""
    user_a = _seed_test_user(db_session, 8804)
    user_b = _seed_test_user(db_session, 8805)

    # User A: High Income
    for m in range(1, 4):
        db_session.add(
            Income(user_id=user_a.id, source="Salary A", amount=Decimal("200000.00"), category="Salary", income_date=datetime.date(2026, m, 1))
        )

    # User B: Insufficient data
    db_session.commit()

    service = CreditworthinessService(db_session)
    prof_a = service.calculate_and_save_profile(user_a.id)
    prof_b = service.calculate_and_save_profile(user_b.id)

    assert prof_a.status == CreditStatus.CALCULATED
    assert prof_a.creditworthiness_score is not None

    assert prof_b.status == CreditStatus.INSUFFICIENT_DATA
    assert prof_b.creditworthiness_score is None
