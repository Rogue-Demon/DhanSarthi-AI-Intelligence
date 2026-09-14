"""
API router for DhanSarthi Creditworthiness Score (DCS).
"""

from __future__ import annotations

from typing import List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.creditworthiness_service import CreditworthinessService
from app.schemas.creditworthiness import (
    CreditworthinessResponse,
    CreditSummaryResponse,
    ScoreComparisonResponse,
    CreditProfileReportResponse,
    CreditHistoryResponse,
    CreditHistorySnapshotResponse,
    ShareConsentRequest,
    ShareConsentResponse,
    CreditDimensionScore,
    DataCoverage,
)
from app.models.creditworthiness import CreditConfidenceLevel

router = APIRouter(prefix="/creditworthiness", tags=["creditworthiness"])


def _build_data_coverage(profile) -> DataCoverage:
    cov = profile.data_coverage or {}
    oldest = cov.get("oldest_record")
    newest = cov.get("newest_record")

    return DataCoverage(
        months_available=cov.get("months_available", profile.months_available),
        months_required_for_high_confidence=cov.get("months_required_for_high_confidence", 6),
        domains_active_count=cov.get("domains_active_count", 0),
        total_domains_count=cov.get("total_domains_count", 6),
        oldest_record=date.fromisoformat(oldest) if oldest and isinstance(oldest, str) else oldest,
        newest_record=date.fromisoformat(newest) if newest and isinstance(newest, str) else newest,
        income_months=cov.get("income_months", 0),
        expense_months=cov.get("expense_months", 0),
        transaction_months=cov.get("transaction_months", 0),
        loan_history_available=cov.get("loan_history_available", False),
        document_evidence_available=cov.get("document_evidence_available", False),
        confidence_score=cov.get("confidence_score", profile.confidence_score),
        confidence_label=CreditConfidenceLevel(cov.get("confidence_label", profile.confidence_label.value if hasattr(profile.confidence_label, "value") else str(profile.confidence_label))),
    )


@router.get("", response_model=CreditworthinessResponse)
def get_creditworthiness(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CreditworthinessResponse:
    """Retrieve the current user's DhanSarthi Creditworthiness Score (DCS) assessment."""
    service = CreditworthinessService(db)
    profile = service.get_or_calculate_credit_profile(current_user.id)

    # Convert dimension dicts to Pydantic objects
    dimensions_dict = {}
    if profile.dimension_scores:
        for k, v in profile.dimension_scores.items():
            if isinstance(v, dict):
                dimensions_dict[k] = CreditDimensionScore(**v)

    data_coverage = _build_data_coverage(profile)
    is_stale = service.is_profile_stale(profile)
    recommendations = service.get_action_recommendations(profile)

    return CreditworthinessResponse(
        user_id=current_user.id,
        creditworthiness_score=profile.creditworthiness_score,
        score_scale="0-100",
        status=profile.status,
        risk_band=profile.risk_band,
        loan_readiness=profile.loan_readiness,
        confidence_score=profile.confidence_score,
        confidence_label=profile.confidence_label,
        data_coverage=data_coverage,
        dti_ratio=profile.dti_ratio,
        savings_rate=profile.savings_rate,
        positive_factors=profile.positive_factors or [],
        risk_factors=profile.risk_factors or [],
        dimension_scores=dimensions_dict,
        action_recommendations=recommendations,
        score_status="STALE" if is_stale else "CURRENT",
        last_calculated_at=profile.last_calculated_at,
        created_at=profile.created_at,
    )


@router.get("/summary", response_model=CreditSummaryResponse)
def get_creditworthiness_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CreditSummaryResponse:
    """Retrieve a lightweight DCS summary for dashboard widgets."""
    service = CreditworthinessService(db)
    profile = service.get_or_calculate_credit_profile(current_user.id)
    is_stale = service.is_profile_stale(profile)

    return CreditSummaryResponse(
        user_id=current_user.id,
        creditworthiness_score=profile.creditworthiness_score,
        status=profile.status,
        risk_band=profile.risk_band,
        confidence_label=profile.confidence_label,
        months_available=profile.months_available,
        loan_readiness=profile.loan_readiness,
        score_status="STALE" if is_stale else "CURRENT",
        last_calculated_at=profile.last_calculated_at,
    )


@router.get("/comparison", response_model=ScoreComparisonResponse)
def get_creditworthiness_comparison(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScoreComparisonResponse:
    """Retrieve snapshot score comparison explaining score changes over time."""
    service = CreditworthinessService(db)
    comp_dict = service.get_score_comparison(current_user.id)
    return ScoreComparisonResponse(**comp_dict)


@router.get("/report", response_model=CreditProfileReportResponse)
def get_creditworthiness_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CreditProfileReportResponse:
    """Retrieve a structured creditworthiness report for prospective lender sharing."""
    service = CreditworthinessService(db)
    report_dict = service.generate_shareable_profile_report(current_user.id)
    return CreditProfileReportResponse(**report_dict)


@router.post("/recalculate", response_model=CreditworthinessResponse)
def recalculate_creditworthiness(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CreditworthinessResponse:
    """Force an on-demand deterministic calculation of the user's DCS score."""
    service = CreditworthinessService(db)
    profile = service.calculate_and_save_profile(current_user.id)

    dimensions_dict = {}
    if profile.dimension_scores:
        for k, v in profile.dimension_scores.items():
            if isinstance(v, dict):
                dimensions_dict[k] = CreditDimensionScore(**v)

    data_coverage = _build_data_coverage(profile)
    recommendations = service.get_action_recommendations(profile)

    return CreditworthinessResponse(
        user_id=current_user.id,
        creditworthiness_score=profile.creditworthiness_score,
        score_scale="0-100",
        status=profile.status,
        risk_band=profile.risk_band,
        loan_readiness=profile.loan_readiness,
        confidence_score=profile.confidence_score,
        confidence_label=profile.confidence_label,
        data_coverage=data_coverage,
        dti_ratio=profile.dti_ratio,
        savings_rate=profile.savings_rate,
        positive_factors=profile.positive_factors or [],
        risk_factors=profile.risk_factors or [],
        dimension_scores=dimensions_dict,
        action_recommendations=recommendations,
        score_status="CURRENT",
        last_calculated_at=profile.last_calculated_at,
        created_at=profile.created_at,
    )


@router.get("/history", response_model=CreditHistoryResponse)
def get_creditworthiness_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CreditHistoryResponse:
    """Retrieve historical snapshots of the user's DCS score over time."""
    service = CreditworthinessService(db)
    snapshots = service.get_score_history(current_user.id)

    items = [
        CreditHistorySnapshotResponse(
            snapshot_date=s.snapshot_date,
            score=s.score,
            status=s.status,
            risk_band=s.risk_band,
            loan_readiness=s.loan_readiness,
            confidence_score=s.confidence_score,
        )
        for s in snapshots
    ]

    return CreditHistoryResponse(user_id=current_user.id, history=items)


@router.post("/share-consent", response_model=ShareConsentResponse)
def record_share_consent(
    req: ShareConsentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ShareConsentResponse:
    """Record explicit user consent for generating a shareable financial credit profile."""
    service = CreditworthinessService(db)
    consent = service.record_share_consent(current_user.id, req.recipient_name)

    return ShareConsentResponse(
        consent_id=consent.id,
        user_id=current_user.id,
        recipient_name=consent.recipient_name,
        consent_granted=consent.consent_granted,
        consented_at=consent.consented_at,
        expires_at=consent.expires_at,
        message=f"Explicit consent granted to share DhanSarthi Creditworthiness Profile with {consent.recipient_name}.",
    )

