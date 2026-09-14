"""REST API Router for DhanSarthi Secure Financial Intelligence.

Endpoints:
  POST  /secure-fi/validate      — Validate a secure access token
  POST  /secure-fi/authenticate   — Verify 4-digit PIN and get session token
  GET   /secure-fi/intelligence   — Retrieve full financial intelligence data

Security:
  - Token validation and PIN verification happen on the backend.
  - The intelligence endpoint requires a dedicated session JWT (not the normal user auth).
  - No financial data is exposed until successful PIN authentication.
  - Generic error messages prevent user/token enumeration.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.secure_intelligence import (
    SecureFinancialIntelligenceResponse,
    SecurePinAuthRequest,
    SecurePinAuthResponse,
    SecureTokenValidateRequest,
    SecureTokenValidateResponse,
)
from app.services.secure_financial_intelligence_service import (
    SecureAccessError,
    SecureAccessLockedError,
    SecureFinancialIntelligenceService,
    SecurePinError,
)

router = APIRouter(
    prefix="/secure-fi",
    tags=["Secure Financial Intelligence"],
)


def _get_secure_fi_service(db: Session = Depends(get_db)) -> SecureFinancialIntelligenceService:
    """Dependency factory for SecureFinancialIntelligenceService."""
    return SecureFinancialIntelligenceService(db)


# ---------------------------------------------------------------------------
# Step 1: Token Validation
# ---------------------------------------------------------------------------


@router.post(
    "/validate",
    response_model=SecureTokenValidateResponse,
    summary="Validate a secure access token",
    description=(
        "Check whether a secure access token exists, is active, and has not expired. "
        "Returns a generic error for any failure — does not reveal token existence."
    ),
)
def validate_token(
    req: SecureTokenValidateRequest,
    svc: SecureFinancialIntelligenceService = Depends(_get_secure_fi_service),
) -> SecureTokenValidateResponse:
    """Validate a secure access token before showing the PIN screen."""
    return svc.validate_token(req.token)


# ---------------------------------------------------------------------------
# Step 2: PIN Authentication
# ---------------------------------------------------------------------------


@router.post(
    "/authenticate",
    response_model=SecurePinAuthResponse,
    summary="Authenticate with 4-digit PIN",
    description=(
        "Verify the 4-digit PIN associated with a secure access token. "
        "Returns a short-lived session JWT on success. "
        "Locks the token after 5 failed attempts."
    ),
)
def authenticate_pin(
    req: SecurePinAuthRequest,
    svc: SecureFinancialIntelligenceService = Depends(_get_secure_fi_service),
) -> SecurePinAuthResponse:
    """Verify the PIN and issue a session token for the intelligence page."""
    try:
        return svc.authenticate_pin(req.token, req.pin)
    except SecureAccessLockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=exc.message,
        )
    except SecurePinError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
        )
    except SecureAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.message,
        )


# ---------------------------------------------------------------------------
# Step 3: Intelligence Data
# ---------------------------------------------------------------------------


@router.get(
    "/intelligence",
    response_model=SecureFinancialIntelligenceResponse,
    summary="Get financial intelligence data",
    description=(
        "Retrieve the complete read-only financial intelligence page data. "
        "Requires a valid session token obtained from the authenticate endpoint. "
        "Pass the session token in the X-Secure-Session header."
    ),
)
def get_intelligence(
    x_secure_session: str = Header(..., alias="X-Secure-Session", description="Session JWT from authenticate"),
    svc: SecureFinancialIntelligenceService = Depends(_get_secure_fi_service),
) -> SecureFinancialIntelligenceResponse:
    """Return full financial intelligence after session authentication."""
    try:
        return svc.get_intelligence(x_secure_session)
    except SecureAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.message,
        )
