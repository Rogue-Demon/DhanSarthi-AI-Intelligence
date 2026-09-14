"""
SQLAlchemy models for DhanSarthi Creditworthiness Score (DCS).
"""

from __future__ import annotations

import enum
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Integer, Float, DateTime, Date, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CreditStatus(str, enum.Enum):
    CALCULATED = "CALCULATED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class RiskBand(str, enum.Enum):
    STRONG = "STRONG"                # 80 - 100
    GOOD = "GOOD"                    # 65 - 79
    MODERATE = "MODERATE"            # 50 - 64
    HIGH_RISK = "HIGH_RISK"          # 35 - 49
    VERY_HIGH_RISK = "VERY_HIGH_RISK"# 0 - 34
    INSUFFICIENT = "INSUFFICIENT"    # Insufficient history


class LoanReadinessState(str, enum.Enum):
    READY = "READY"
    NEARLY_READY = "NEARLY_READY"
    BUILD_HISTORY = "BUILD_HISTORY"
    HIGH_RISK = "HIGH_RISK"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class CreditConfidenceLevel(str, enum.Enum):
    HIGH = "HIGH"      # 0.80 - 1.00
    MEDIUM = "MEDIUM"  # 0.50 - 0.79
    LOW = "LOW"        # 0.00 - 0.49


class CreditProfile(Base):
    """Stores the current calculated Creditworthiness Profile for a user."""

    __tablename__ = "credit_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)

    creditworthiness_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[CreditStatus] = mapped_column(SQLEnum(CreditStatus), default=CreditStatus.INSUFFICIENT_DATA, nullable=False)
    risk_band: Mapped[RiskBand] = mapped_column(SQLEnum(RiskBand), default=RiskBand.INSUFFICIENT, nullable=False)
    loan_readiness: Mapped[LoanReadinessState] = mapped_column(SQLEnum(LoanReadinessState), default=LoanReadinessState.INSUFFICIENT_DATA, nullable=False)

    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence_label: Mapped[CreditConfidenceLevel] = mapped_column(SQLEnum(CreditConfidenceLevel), default=CreditConfidenceLevel.LOW, nullable=False)

    months_available: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dti_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    savings_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    positive_factors: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    risk_factors: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    dimension_scores: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    data_coverage: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    last_calculated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", backref="credit_profile")


class CreditScoreSnapshot(Base):
    """Historical snapshot of a user's DCS score over time for trend analysis."""

    __tablename__ = "credit_score_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, default=date.today, index=True, nullable=False)

    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[CreditStatus] = mapped_column(SQLEnum(CreditStatus), nullable=False)
    risk_band: Mapped[RiskBand] = mapped_column(SQLEnum(RiskBand), nullable=False)
    loan_readiness: Mapped[LoanReadinessState] = mapped_column(SQLEnum(LoanReadinessState), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    dimension_scores: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", backref="credit_score_snapshots")


class CreditShareConsent(Base):
    """Records explicit user consent for sharing a creditworthiness profile."""

    __tablename__ = "credit_share_consents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    recipient_name: Mapped[str] = mapped_column(String(100), nullable=False)
    consent_granted: Mapped[bool] = mapped_column(nullable=False, default=True)
    consented_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user = relationship("User", backref="credit_share_consents")
