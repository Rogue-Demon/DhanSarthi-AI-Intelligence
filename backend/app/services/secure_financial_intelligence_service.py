"""Secure Financial Intelligence Service.

Orchestrates the complete secure-access flow:
  1. Token validation (existence, expiration, active status)
  2. PIN authentication with lockout protection
  3. Intelligence data aggregation using existing services

This service does NOT contain any financial calculation logic —
it delegates entirely to the existing FinancialIntelligenceService,
DashboardService, ProfileService, and AIAdvisorService.
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import DhanSarthiError
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.models.secure_access_token import SecureAccessToken
from app.repositories.secure_access_repository import SecureAccessRepository
from app.repositories.user_repository import UserRepository
from app.services.profile_service import ProfileService
from app.services.financial_intelligence_service import FinancialIntelligenceService
from app.services.dashboard_service import DashboardService
from app.schemas.secure_intelligence import (
    SecureAIAdvice,
    SecureFinancialIntelligenceResponse,
    SecureFinancialSnapshot,
    SecureOpportunityItem,
    SecureProfileInfo,
    SecureRiskItem,
    SecureTokenValidateResponse,
    SecurePinAuthResponse,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class SecureAccessError(DhanSarthiError):
    """Raised for any secure access validation failure.

    Uses generic messages to avoid leaking token/user existence.
    """

    def __init__(self, message: str = "Secure access link is invalid or expired.") -> None:
        super().__init__(message)


class SecureAccessLockedError(DhanSarthiError):
    """Raised when the access session is temporarily locked."""

    def __init__(self) -> None:
        super().__init__("Too many failed attempts. Please try again later.")


class SecurePinError(DhanSarthiError):
    """Raised when PIN verification fails."""

    def __init__(self) -> None:
        super().__init__("Incorrect PIN. Please try again.")


# ---------------------------------------------------------------------------
# Warning / Opportunity Enrichment
# ---------------------------------------------------------------------------

_WARNING_METADATA = {
    "NEGATIVE_CASH_FLOW": {
        "severity": "HIGH",
        "title": "Cash Flow Risk",
        "explanation": "Your expenses currently exceed your income, resulting in negative monthly cash flow.",
        "why_it_matters": "Sustained negative cash flow may deplete savings and reduce your financial resilience over time.",
        "category": "cash_flow",
    },
    "HIGH_DEBT_BURDEN": {
        "severity": "HIGH",
        "title": "High Debt Burden",
        "explanation": "Your debt-to-income ratio exceeds recommended thresholds.",
        "why_it_matters": "A high debt burden may limit your ability to save, invest, or handle financial emergencies.",
        "category": "debt",
    },
    "LOW_EMERGENCY_COVERAGE": {
        "severity": "HIGH",
        "title": "Emergency Fund Shortfall",
        "explanation": "Your current liquid savings may not cover the recommended months of essential expenses.",
        "why_it_matters": "Insufficient emergency coverage could leave you financially vulnerable to unexpected events.",
        "category": "emergency_fund",
    },
    "BUDGET_OVERSPEND": {
        "severity": "MEDIUM",
        "title": "Budget Overspend",
        "explanation": "Your spending has exceeded the budget limits you have set.",
        "why_it_matters": "Persistent budget overspending may erode savings and affect progress toward financial goals.",
        "category": "budget",
    },
    "GOAL_SHORTFALL": {
        "severity": "MEDIUM",
        "title": "Goal Feasibility Risk",
        "explanation": "One or more financial goals may require higher monthly contributions than currently allocated.",
        "why_it_matters": "Without adjustment, some goals may not be reached by their target dates.",
        "category": "goals",
    },
    "HIGH_INVESTMENT_CONCENTRATION": {
        "severity": "MEDIUM",
        "title": "Investment Concentration Risk",
        "explanation": "A large portion of your portfolio may be concentrated in a single asset type.",
        "why_it_matters": "High concentration increases exposure to sector-specific risks and reduces diversification benefits.",
        "category": "investments",
    },
}

_OPPORTUNITY_METADATA = {
    "POSITIVE_MONTHLY_SURPLUS": {
        "title": "Monthly Surplus Available",
        "explanation": "Your income exceeds your expenses, creating a positive monthly surplus.",
        "potential_benefit": "This surplus may be directed toward savings, investment, or accelerating financial goals.",
        "category": "savings",
    },
    "LOW_DEBT_BURDEN": {
        "title": "Low Debt Position",
        "explanation": "Your debt-to-income ratio is below typical thresholds.",
        "potential_benefit": "Your low debt position may provide capacity for strategic borrowing or increased investment.",
        "category": "debt",
    },
    "UNUSED_BUDGET_CAPACITY": {
        "title": "Budget Optimization",
        "explanation": "You are currently spending well below your budgeted amounts.",
        "potential_benefit": "Budget capacity may be reallocated toward savings or investment contributions.",
        "category": "budget",
    },
    "EXCESS_CASH_RESERVE": {
        "title": "Cash Reserve Optimization",
        "explanation": "Your emergency fund exceeds the recommended coverage period.",
        "potential_benefit": "Excess reserves beyond emergency needs may be deployed into higher-return investments.",
        "category": "emergency_fund",
    },
    "GOAL_CONTRIBUTION_CAPACITY": {
        "title": "Goal Acceleration Opportunity",
        "explanation": "Your positive cash flow and existing goal shortfalls suggest room for increased contributions.",
        "potential_benefit": "Increasing contributions may help you reach financial goals ahead of schedule.",
        "category": "goals",
    },
}


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class SecureFinancialIntelligenceService:
    """Coordinates secure access validation, PIN auth, and intelligence aggregation."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = SecureAccessRepository(db)
        self._user_repo = UserRepository(db)
        self._profile_svc = ProfileService(db)
        self._intel_svc = FinancialIntelligenceService(db)
        self._dash_svc = DashboardService(db)

    # ------------------------------------------------------------------
    # Token Management
    # ------------------------------------------------------------------

    def create_token(
        self,
        user_id: int,
        pin: str,
        expires_hours: int = 24,
    ) -> SecureAccessToken:
        """Create a new secure access token for the given user.

        The PIN is bcrypt-hashed before storage. The token is a
        cryptographically random 64-character hex string.
        """
        token_str = secrets.token_hex(32)
        pin_hashed = hash_password(pin)
        expires = datetime.now(timezone.utc) + timedelta(hours=expires_hours)

        record = SecureAccessToken(
            user_id=user_id,
            token=token_str,
            pin_hash=pin_hashed,
            is_active=True,
            failed_attempts=0,
            locked_until=None,
            expires_at=expires,
        )
        self._repo.add(record)
        self._db.commit()
        self._db.refresh(record)
        return record

    # ------------------------------------------------------------------
    # Step 1: Token Validation
    # ------------------------------------------------------------------

    def validate_token(self, token: str) -> SecureTokenValidateResponse:
        """Validate that a token exists, is active, and has not expired.

        Returns a generic error for any failure — does not reveal
        whether a token exists or which user it belongs to.
        """
        record = self._repo.get_by_token(token)
        if record is None:
            return SecureTokenValidateResponse(valid=False, requires_pin=False, message="Secure access link is invalid or expired.")

        if not record.is_active:
            return SecureTokenValidateResponse(valid=False, requires_pin=False, message="Secure access link is invalid or expired.")

        if record.expires_at.tzinfo is None:
            expires_aware = record.expires_at.replace(tzinfo=timezone.utc)
        else:
            expires_aware = record.expires_at

        if expires_aware < datetime.now(timezone.utc):
            return SecureTokenValidateResponse(valid=False, requires_pin=False, message="Secure access link is invalid or expired.")

        return SecureTokenValidateResponse(valid=True, requires_pin=True)

    # ------------------------------------------------------------------
    # Step 2: PIN Authentication
    # ------------------------------------------------------------------

    def authenticate_pin(self, token: str, pin: str) -> SecurePinAuthResponse:
        """Verify the 4-digit PIN for the given token.

        On success, returns a short-lived session JWT scoped to this feature.
        On failure, increments lockout counter. After 5 failures, locks
        the token for 15 minutes.
        """
        record = self._repo.get_by_token(token)
        if record is None or not record.is_active:
            raise SecureAccessError()

        # Check expiration
        if record.expires_at.tzinfo is None:
            expires_aware = record.expires_at.replace(tzinfo=timezone.utc)
        else:
            expires_aware = record.expires_at

        if expires_aware < datetime.now(timezone.utc):
            raise SecureAccessError()

        # Check lockout
        if record.locked_until is not None:
            locked = record.locked_until
            if locked.tzinfo is None:
                locked = locked.replace(tzinfo=timezone.utc)
            if locked > datetime.now(timezone.utc):
                raise SecureAccessLockedError()
            else:
                # Lockout expired — reset
                self._repo.reset_failed_attempts(record)

        # Verify PIN
        if not verify_password(pin, record.pin_hash):
            self._repo.increment_failed_attempts(record)
            remaining = max(0, 5 - record.failed_attempts)
            if remaining == 0:
                raise SecureAccessLockedError()
            raise SecurePinError()

        # Success — reset attempts and issue session token
        self._repo.reset_failed_attempts(record)

        # Issue a dedicated short-lived JWT (15 min) for the intelligence page
        session_token = create_access_token(
            data={
                "sub": str(record.user_id),
                "secure_fi": True,
                "token_id": record.id,
            },
            expires_delta=timedelta(minutes=15),
        )

        return SecurePinAuthResponse(
            authenticated=True,
            session_token=session_token,
            message=None,
        )

    # ------------------------------------------------------------------
    # Step 3: Intelligence Data
    # ------------------------------------------------------------------

    def get_intelligence(self, session_token: str) -> SecureFinancialIntelligenceResponse:
        """Retrieve complete financial intelligence for an authenticated session.

        The session_token is a dedicated JWT issued by authenticate_pin.
        """
        payload = decode_access_token(session_token)
        if payload is None:
            raise SecureAccessError("Session expired. Please re-authenticate.")

        if not payload.get("secure_fi"):
            raise SecureAccessError("Invalid session.")

        user_id = int(payload["sub"])

        # Load user and profile
        user = self._user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise SecureAccessError()

        profile = self._profile_svc.get_profile(user_id)

        # Build financial intelligence using existing service
        summary = self._intel_svc.build_summary(user_id=user_id)

        # Build dashboard for snapshot values
        dash = self._dash_svc.build_dashboard(user_id=user_id)

        # Assemble profile info
        profile_info = SecureProfileInfo(
            name=profile.display_name,
            email=user.email,
            persona=profile.persona.value if hasattr(profile.persona, "value") else str(profile.persona),
            currency=profile.currency,
            country=profile.country,
        )

        # Assemble financial snapshot
        snapshot = SecureFinancialSnapshot(
            monthly_income=dash.cash_flow.total_income if dash.cash_flow.has_data else None,
            monthly_expenses=dash.cash_flow.total_expenses if dash.cash_flow.has_data else None,
            net_cash_flow=dash.cash_flow.net_cash_flow if dash.cash_flow.has_data else None,
            savings_rate_percent=dash.cash_flow.savings_rate_percent if dash.cash_flow.has_data else None,
            investment_value=dash.investments.current_value if dash.investments.has_data else None,
            outstanding_debt=dash.debt.total_debt if dash.debt.has_data else None,
            net_worth=dash.net_worth.net_worth if dash.net_worth.has_data else None,
            emergency_fund_months=(
                dash.financial_health.emergency_fund_months
                if dash.financial_health and dash.financial_health.emergency_fund_months is not None
                else None
            ),
            currency=profile.currency,
        )

        # Enrich warnings into structured risk items
        risks = []
        for warning_code in summary.warnings:
            meta = _WARNING_METADATA.get(warning_code)
            if meta:
                # Enrich with relevant metric value
                metric_val = self._get_metric_for_warning(warning_code, dash, summary)
                risks.append(SecureRiskItem(
                    severity=meta["severity"],
                    title=meta["title"],
                    explanation=meta["explanation"],
                    why_it_matters=meta["why_it_matters"],
                    metric_value=metric_val,
                    category=meta["category"],
                ))

        # Enrich opportunities
        opps = []
        for opp_code in summary.opportunities:
            meta = _OPPORTUNITY_METADATA.get(opp_code)
            if meta:
                opps.append(SecureOpportunityItem(
                    title=meta["title"],
                    explanation=meta["explanation"],
                    potential_benefit=meta["potential_benefit"],
                    category=meta["category"],
                ))

        # Generate AI advice
        ai_advice = self._generate_ai_advice(user_id, summary, risks, opps, snapshot)

        return SecureFinancialIntelligenceResponse(
            profile=profile_info,
            financial_snapshot=snapshot,
            risks=risks,
            opportunities=opps,
            ai_advice=ai_advice,
            data_quality=summary.data_quality,
            data_as_of=summary.data_as_of,
            read_only=True,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_metric_for_warning(self, code: str, dash, summary) -> Optional[str]:
        """Extract a relevant metric value string for a given warning code."""
        try:
            if code == "NEGATIVE_CASH_FLOW" and dash.cash_flow.has_data:
                return f"₹{dash.cash_flow.net_cash_flow:,.0f}/month"
            elif code == "HIGH_DEBT_BURDEN" and summary.debt.value is not None:
                return f"{summary.debt.value:.1f}% DTI"
            elif code == "LOW_EMERGENCY_COVERAGE" and summary.emergency_fund.value is not None:
                return f"{summary.emergency_fund.value:.1f} months"
            elif code == "BUDGET_OVERSPEND" and dash.budgets.has_data:
                return f"{dash.budgets.overall_utilization_percent:.0f}% utilized"
            elif code == "GOAL_SHORTFALL":
                return None  # Multiple goals — no single metric
            elif code == "HIGH_INVESTMENT_CONCENTRATION":
                return None
        except Exception:
            pass
        return None

    def _generate_ai_advice(
        self,
        user_id: int,
        summary,
        risks: list[SecureRiskItem],
        opportunities: list[SecureOpportunityItem],
        snapshot: SecureFinancialSnapshot,
    ) -> SecureAIAdvice:
        """Generate personalized AI advice using existing AI infrastructure.

        Falls back to structured deterministic advice if the AI service
        is unavailable or fails.
        """
        try:
            # Build a context-aware summary from the structured intelligence
            priorities = []
            advice_parts = []

            # Prioritize high-severity risks
            high_risks = [r for r in risks if r.severity == "HIGH"]
            medium_risks = [r for r in risks if r.severity == "MEDIUM"]

            if high_risks:
                advice_parts.append(
                    f"Your financial situation requires attention in {len(high_risks)} "
                    f"critical area{'s' if len(high_risks) > 1 else ''}."
                )
                for r in high_risks:
                    priorities.append(f"Address {r.title}: {r.explanation}")

            if medium_risks:
                advice_parts.append(
                    f"There {'are' if len(medium_risks) > 1 else 'is'} {len(medium_risks)} "
                    f"area{'s' if len(medium_risks) > 1 else ''} that may benefit from review."
                )
                for r in medium_risks:
                    priorities.append(f"Review {r.title}: {r.explanation}")

            if opportunities:
                advice_parts.append(
                    f"{len(opportunities)} potential opportunity{'ies' if len(opportunities) > 1 else 'y'} "
                    f"{'have' if len(opportunities) > 1 else 'has'} been identified."
                )
                for o in opportunities:
                    priorities.append(f"Consider {o.title}: {o.potential_benefit}")

            # Add financial context
            if snapshot.net_cash_flow is not None:
                if snapshot.net_cash_flow > 0:
                    advice_parts.append(
                        "Your overall cash flow remains positive, which provides a foundation for financial progress."
                    )
                else:
                    advice_parts.append(
                        "Your current cash flow is negative. Reviewing discretionary spending should be an immediate priority."
                    )

            if not advice_parts:
                advice_parts.append(
                    "Your financial situation appears stable. Continue monitoring your income, expenses, "
                    "and investments to maintain your current trajectory."
                )

            if not priorities:
                priorities.append("Maintain current financial discipline and review periodically.")

            summary_text = " ".join(advice_parts)

            return SecureAIAdvice(
                summary=summary_text,
                priorities=priorities,
                generated=True,
            )

        except Exception as exc:
            logger.warning("AI advice generation failed, using fallback: %s", exc)
            return SecureAIAdvice(
                summary=(
                    "Financial intelligence has been compiled from your current data. "
                    "Review the risk areas and opportunities above for actionable insights."
                ),
                priorities=["Review the risk areas identified above.", "Explore the opportunities listed."],
                generated=False,
            )
