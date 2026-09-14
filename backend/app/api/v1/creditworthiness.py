"""
API router for DhanSarthi Creditworthiness Score (DCS).
"""

from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.creditworthiness_service import CreditworthinessService
from app.schemas.creditworthiness import (
    CreditworthinessResponse,
    CreditHistoryResponse,
    CreditHistorySnapshotResponse,
    ShareConsentRequest,
    ShareConsentResponse,
    CreditDimensionScore,
    DataCoverage,
)
from app.models.creditworthiness import CreditConfidenceLevel

router = APIRouter(prefix="/creditworthiness", tags=["creditworthiness"])


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

    # Format coverage
    cov = profile.data_coverage or {}
    data_coverage = DataCoverage(
        months_available=cov.get("months_available", profile.months_available),
        months_required_for_high_confidence=cov.get("months_required_for_high_confidence", 6),
        domains_active_count=cov.get("domains_active_count", 0),
        total_domains_count=cov.get("total_domains_count", 6),
        confidence_score=cov.get("confidence_score", profile.confidence_score),
        confidence_label=CreditConfidenceLevel(cov.get("confidence_label", profile.confidence_label.value if hasattr(profile.confidence_label, "value") else str(profile.confidence_label))),
    )

    return CreditworthinessResponse(
        user_id=current_user.id,
        creditworthiness_score=profile.creditworthiness_score,
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
        last_calculated_at=profile.last_calculated_at,
        created_at=profile.created_at,
    )


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

    cov = profile.data_coverage or {}
    data_coverage = DataCoverage(
        months_available=cov.get("months_available", profile.months_available),
        months_required_for_high_confidence=cov.get("months_required_for_high_confidence", 6),
        domains_active_count=cov.get("domains_active_count", 0),
        total_domains_count=cov.get("total_domains_count", 6),
        confidence_score=cov.get("confidence_score", profile.confidence_score),
        confidence_label=CreditConfidenceLevel(cov.get("confidence_label", profile.confidence_label.value if hasattr(profile.confidence_label, "value") else str(profile.confidence_label))),
    )

    return CreditworthinessResponse(
        user_id=current_user.id,
        creditworthiness_score=profile.creditworthiness_score,
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
        message=f"Explicit consent granted to share DhanSarthi Creditworthiness Profile with {consent.recipient_name}.",
    )
