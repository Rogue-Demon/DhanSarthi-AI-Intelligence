"""Pydantic schemas for the Secure Financial Intelligence API.

These schemas define the request/response contract for the secure
access flow: token validation → PIN authentication → intelligence data.

No internal database objects or unnecessary financial data is exposed.
"""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Token Validation
# ---------------------------------------------------------------------------


class SecureTokenValidateRequest(BaseModel):
    """Request to validate an opaque secure access token."""
    token: str = Field(..., min_length=1, description="Opaque secure access token")


class SecureTokenValidateResponse(BaseModel):
    """Response indicating whether a token is valid and requires PIN."""
    valid: bool
    requires_pin: bool = True
    message: Optional[str] = None


# ---------------------------------------------------------------------------
# PIN Authentication
# ---------------------------------------------------------------------------


class SecurePinAuthRequest(BaseModel):
    """Request to authenticate with a 4-digit PIN."""
    token: str = Field(..., min_length=1, description="Opaque secure access token")
    pin: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$", description="4-digit PIN")


class SecurePinAuthResponse(BaseModel):
    """Response after PIN authentication attempt."""
    authenticated: bool
    session_token: Optional[str] = Field(
        default=None,
        description="Short-lived JWT for accessing the intelligence data. Only returned on success.",
    )
    message: Optional[str] = None


# ---------------------------------------------------------------------------
# Intelligence Data — Profile
# ---------------------------------------------------------------------------


class SecureProfileInfo(BaseModel):
    """Sanitized user profile information for the intelligence page."""
    name: str
    email: str
    persona: str
    currency: str
    country: str


# ---------------------------------------------------------------------------
# Intelligence Data — Financial Snapshot
# ---------------------------------------------------------------------------


class SecureFinancialSnapshot(BaseModel):
    """Concise summary of the user's current financial situation."""
    monthly_income: Optional[Decimal] = None
    monthly_expenses: Optional[Decimal] = None
    net_cash_flow: Optional[Decimal] = None
    savings_rate_percent: Optional[Decimal] = None
    investment_value: Optional[Decimal] = None
    outstanding_debt: Optional[Decimal] = None
    net_worth: Optional[Decimal] = None
    emergency_fund_months: Optional[Decimal] = None
    currency: str = "INR"


# ---------------------------------------------------------------------------
# Intelligence Data — Risks
# ---------------------------------------------------------------------------


class SecureRiskItem(BaseModel):
    """A single financial risk area identified by the intelligence engine."""
    severity: str = Field(..., description="HIGH, MEDIUM, or LOW")
    title: str
    explanation: str
    why_it_matters: str
    metric_value: Optional[str] = None
    category: str


# ---------------------------------------------------------------------------
# Intelligence Data — Opportunities
# ---------------------------------------------------------------------------


class SecureOpportunityItem(BaseModel):
    """A single financial opportunity identified by the intelligence engine."""
    title: str
    explanation: str
    potential_benefit: str
    category: str


# ---------------------------------------------------------------------------
# Intelligence Data — AI Advice
# ---------------------------------------------------------------------------


class SecureAIAdvice(BaseModel):
    """Personalized AI-generated financial advice."""
    summary: str = Field(..., description="Natural-language advice summary")
    priorities: List[str] = Field(default_factory=list, description="Prioritized action items")
    generated: bool = Field(
        default=True,
        description="True if AI generated this. False if fallback was used.",
    )


# ---------------------------------------------------------------------------
# Top-level Response
# ---------------------------------------------------------------------------


class SecureFinancialIntelligenceResponse(BaseModel):
    """Complete read-only financial intelligence response.

    This is the primary response returned after successful PIN authentication.
    Contains only the sanitized data needed for the intelligence page.
    """
    profile: SecureProfileInfo
    financial_snapshot: SecureFinancialSnapshot
    risks: List[SecureRiskItem] = Field(default_factory=list)
    opportunities: List[SecureOpportunityItem] = Field(default_factory=list)
    ai_advice: SecureAIAdvice
    data_quality: str = Field(..., description="COMPLETE, GOOD, PARTIAL, or LIMITED")
    data_as_of: str = Field(..., description="ISO-8601 timestamp of data freshness")
    read_only: bool = Field(default=True, description="Always True — this page is read-only")
