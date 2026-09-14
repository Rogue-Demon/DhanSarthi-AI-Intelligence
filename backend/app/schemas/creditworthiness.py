"""
Pydantic v2 schemas for DhanSarthi Creditworthiness Score (DCS).
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.models.creditworthiness import (
    CreditStatus,
    CreditDimensionStatus,
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
    status: CreditDimensionStatus = Field(default=CreditDimensionStatus.AVAILABLE, description="Dimension status")
    explanation: Optional[str] = Field(None, description="Data-grounded explanation")


class DataCoverage(BaseModel):
    months_available: int = Field(..., description="Distinct active months in DhanSarthi")
    months_required_for_high_confidence: int = Field(default=6)
    domains_active_count: int = Field(..., description="Count of active financial domains")
    total_domains_count: int = Field(default=6)
    oldest_record: Optional[date] = Field(None, description="Date of oldest financial record")
    newest_record: Optional[date] = Field(None, description="Date of newest financial record")
    income_months: int = Field(0, description="Months with active income records")
    expense_months: int = Field(0, description="Months with active expense records")
    transaction_months: int = Field(0, description="Months with active transaction records")
    loan_history_available: bool = Field(False, description="Whether loan history is present")
    document_evidence_available: bool = Field(False, description="Whether income document evidence is verified")
    confidence_score: float = Field(..., description="Confidence percentage (0.0 - 1.0)")
    confidence_label: CreditConfidenceLevel = Field(...)


class CreditworthinessResponse(BaseModel):
    user_id: int
    creditworthiness_score: Optional[int] = Field(None, description="0 - 100 internal score or null if INSUFFICIENT_DATA")
    score_scale: str = Field(default="0-100", description="Native score scale (0-100)")
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
    action_recommendations: List[str] = Field(default_factory=list, description="Deterministic actionable recommendations")

    score_status: str = Field(default="CURRENT", description="CURRENT or STALE")

    disclaimer: str = Field(
        default="This is DhanSarthi's internal creditworthiness assessment. It is not a CIBIL score, credit bureau score, or guarantee of loan approval."
    )

    last_calculated_at: datetime
    created_at: datetime


class CreditSummaryResponse(BaseModel):
    user_id: int
    creditworthiness_score: Optional[int] = Field(None, description="0 - 100 score or null if INSUFFICIENT_DATA")
    status: CreditStatus
    risk_band: RiskBand
    confidence_label: CreditConfidenceLevel
    months_available: int
    loan_readiness: LoanReadinessState
    score_status: str = Field(default="CURRENT", description="CURRENT or STALE")
    last_calculated_at: Optional[datetime] = None
    disclaimer: str = Field(
        default="This is DhanSarthi's internal creditworthiness assessment. It is not a CIBIL score, credit bureau score, or guarantee of loan approval."
    )


class ScoreComparisonResponse(BaseModel):
    user_id: int
    has_comparison: bool = Field(..., description="True if at least 2 historical snapshots exist")
    previous_score: Optional[int] = None
    current_score: Optional[int] = None
    score_delta: Optional[int] = None
    previous_date: Optional[date] = None
    current_date: Optional[date] = None
    dimension_changes: Dict[str, float] = Field(default_factory=dict, description="Score change per dimension")
    explanation_summary: str = Field(..., description="Deterministic change explanation summary")


class CreditProfileReportResponse(BaseModel):
    user_id: int
    generated_at: datetime
    creditworthiness_score: Optional[int] = None
    status: CreditStatus
    risk_band: RiskBand
    confidence_label: CreditConfidenceLevel
    loan_readiness: LoanReadinessState
    months_available: int
    dti_ratio: Optional[float] = None
    savings_rate: Optional[float] = None
    positive_factors: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    action_recommendations: List[str] = Field(default_factory=list)
    financial_summary: Dict[str, Any] = Field(default_factory=dict)
    repayment_indicators: Dict[str, Any] = Field(default_factory=dict)
    data_coverage: Dict[str, Any] = Field(default_factory=dict)
    disclaimer: str = Field(
        default="This is DhanSarthi's internal creditworthiness assessment. It is not a CIBIL score, credit bureau score, or guarantee of loan approval."
    )


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
    expires_at: Optional[datetime] = None
    message: str = Field(default="Consent recorded. Secure financial credit profile prepared for user-initiated sharing.")

