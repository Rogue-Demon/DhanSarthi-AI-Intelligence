"""
Pydantic v2 schemas for DhanSarthi Creditworthiness Score (DCS).
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.models.creditworthiness import (
    CreditStatus,
    RiskBand,
    LoanReadinessState,
    CreditConfidenceLevel,
)


class CreditDimensionScore(BaseModel):
    name: str = Field(..., description="Dimension key name")
    label: str = Field(..., description="User-facing display title")
    weight: float = Field(..., description="Dimension weight percentage (0.0 - 1.0)")
    score: float = Field(..., description="Normalized dimension score (0 - 100)")
    weighted_score: float = Field(..., description="Contribution to total score")
    description: str = Field(..., description="Explainable description")


class DataCoverage(BaseModel):
    months_available: int = Field(..., description="Distinct active months in DhanSarthi")
    months_required_for_high_confidence: int = Field(default=6)
    domains_active_count: int = Field(..., description="Count of active financial domains")
    total_domains_count: int = Field(default=6)
    confidence_score: float = Field(..., description="Confidence percentage (0.0 - 1.0)")
    confidence_label: CreditConfidenceLevel = Field(...)


class CreditworthinessResponse(BaseModel):
    user_id: int
    creditworthiness_score: Optional[int] = Field(None, description="0 - 100 internal score or null if INSUFFICIENT_DATA")
    status: CreditStatus
    risk_band: RiskBand
    loan_readiness: LoanReadinessState

    confidence_score: float
    confidence_label: CreditConfidenceLevel
    data_coverage: DataCoverage

    dti_ratio: Optional[float] = Field(None, description="Debt-to-income ratio (0.0 - 1.0)")
    savings_rate: Optional[float] = Field(None, description="Savings rate percentage")

    positive_factors: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    dimension_scores: Dict[str, CreditDimensionScore] = Field(default_factory=dict)

    disclaimer: str = Field(
        default="DhanSarthi Creditworthiness Score (DCS) is an internal, explainable financial health assessment based on available user records. It is NOT an official credit bureau score (e.g. CIBIL, Experian) and does not guarantee loan approval."
    )

    last_calculated_at: datetime
    created_at: datetime


class CreditHistorySnapshotResponse(BaseModel):
    snapshot_date: date
    score: Optional[int]
    status: CreditStatus
    risk_band: RiskBand
    loan_readiness: LoanReadinessState
    confidence_score: float


class CreditHistoryResponse(BaseModel):
    user_id: int
    history: List[CreditHistorySnapshotResponse] = Field(default_factory=list)


class ShareConsentRequest(BaseModel):
    recipient_name: str = Field(..., min_length=2, max_length=100, description="Name of prospective lender or institution")


class ShareConsentResponse(BaseModel):
    consent_id: int
    user_id: int
    recipient_name: str
    consent_granted: bool
    consented_at: datetime
    message: str = Field(default="Consent recorded. Secure financial credit profile prepared for user-initiated sharing.")
