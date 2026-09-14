"""
DhanSarthi Creditworthiness Score (DCS) Engine.

100% deterministic backend evaluation service that analyzes authentic user records
from PostgreSQL (Incomes, Expenses, Loans, Liabilities, Assets, Investments, Budgets,
Transactions, and Documents) to produce an explainable creditworthiness assessment.

CRITICAL RULES:
1. NEVER use mock, random, or LLM-generated numerical scores.
2. Insufficient data (< 3 active months or < 3 records) yields status = INSUFFICIENT_DATA and score = null.
3. User data is strictly isolated by user_id.
"""

from __future__ import annotations

import math
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.income import Income
from app.models.expense import Expense
from app.models.transaction import Transaction
from app.models.loan import Loan, LoanStatus
from app.models.liability import Liability
from app.models.asset import Asset
from app.models.investment import Investment
from app.models.budget import Budget
from app.models.financial_document import FinancialDocument, DocumentStatus
from app.models.enums import DocumentType
from app.models.creditworthiness import (
    CreditProfile,
    CreditScoreSnapshot,
    CreditShareConsent,
    CreditStatus,
    CreditDimensionStatus,
    RiskBand,
    LoanReadinessState,
    CreditConfidenceLevel,
)
from app.schemas.creditworthiness import (
    CreditworthinessResponse,
    CreditDimensionScore,
    DataCoverage,
)


class CreditworthinessService:
    """Service providing deterministic creditworthiness evaluation and snapshot management."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_calculate_credit_profile(self, user_id: int, force_recalculate: bool = False) -> CreditProfile:
        """Fetch existing credit profile or trigger calculation if stale/missing."""
        profile = (
            self.db.query(CreditProfile)
            .filter(CreditProfile.user_id == user_id)
            .first()
        )

        # Recalculate if profile missing, force requested, or last calculation older than 24 hours
        now_utc = datetime.now(timezone.utc)
        if not profile or force_recalculate:
            profile = self.calculate_and_save_profile(user_id)
        elif profile.last_calculated_at:
            last_calc = profile.last_calculated_at
            if last_calc.tzinfo is None:
                last_calc = last_calc.replace(tzinfo=timezone.utc)
            if (now_utc - last_calc) > timedelta(hours=24):
                profile = self.calculate_and_save_profile(user_id)

        return profile

    def calculate_and_save_profile(self, user_id: int) -> CreditProfile:
        """
        Execute full deterministic evaluation across 6 financial dimensions.
        Saves updated CreditProfile and appends CreditScoreSnapshot.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} does not exist.")

        # 1. Fetch authentic user data records
        incomes = self.db.query(Income).filter(Income.user_id == user_id).all()
        expenses = self.db.query(Expense).filter(Expense.user_id == user_id).all()
        loans = self.db.query(Loan).filter(Loan.user_id == user_id).all()
        liabilities = self.db.query(Liability).filter(Liability.user_id == user_id).all()
        assets = self.db.query(Asset).filter(Asset.user_id == user_id).all()
        investments = self.db.query(Investment).filter(Investment.user_id == user_id).all()
        budgets = self.db.query(Budget).filter(Budget.user_id == user_id).all()
        transactions = self.db.query(Transaction).filter(Transaction.user_id == user_id).all()
        documents = self.db.query(FinancialDocument).filter(FinancialDocument.user_id == user_id).all()

        total_records = (
            len(incomes)
            + len(expenses)
            + len(loans)
            + len(liabilities)
            + len(assets)
            + len(investments)
            + len(transactions)
        )

        # Calculate distinct active calendar months per domain and overall
        income_dates = [i.income_date for i in incomes if i.income_date]
        expense_dates = [e.expense_date for e in expenses if e.expense_date]
        txn_dates = [t.transaction_date for t in transactions if t.transaction_date]

        income_months_set = {(d.year, d.month) for d in income_dates}
        expense_months_set = {(d.year, d.month) for d in expense_dates}
        txn_months_set = {(d.year, d.month) for d in txn_dates}

        all_dates: List[date] = income_dates + expense_dates + txn_dates
        all_months_set = income_months_set | expense_months_set | txn_months_set
        months_available = len(all_months_set)

        oldest_rec = min(all_dates) if all_dates else None
        newest_rec = max(all_dates) if all_dates else None

        loan_history_available = len(loans) > 0 or len(liabilities) > 0
        has_verified_doc = any(
            doc.document_type in (DocumentType.SALARY_SLIP, DocumentType.TAX_DOCUMENT, DocumentType.BUSINESS_FINANCIAL_DOCUMENT)
            and doc.status in (DocumentStatus.CONFIRMED, DocumentStatus.EXTRACTED)
            for doc in documents
        )

        active_domains_count = sum([
            1 if len(incomes) > 0 else 0,
            1 if len(expenses) > 0 else 0,
            1 if loan_history_available else 0,
            1 if len(assets) > 0 or len(investments) > 0 else 0,
            1 if len(budgets) > 0 else 0,
            1 if has_verified_doc else 0,
        ])

        # 2. Check Insufficient Data Thresholds (< 3 months or < 3 total records)
        if total_records < 3 or months_available < 3:
            profile = (
                self.db.query(CreditProfile)
                .filter(CreditProfile.user_id == user_id)
                .first()
            )
            if not profile:
                profile = CreditProfile(user_id=user_id)
                self.db.add(profile)

            profile.creditworthiness_score = None
            profile.status = CreditStatus.INSUFFICIENT_DATA
            profile.risk_band = RiskBand.INSUFFICIENT
            profile.loan_readiness = LoanReadinessState.INSUFFICIENT_DATA
            profile.confidence_score = 0.0
            profile.confidence_label = CreditConfidenceLevel.LOW
            profile.months_available = months_available
            profile.dti_ratio = None
            profile.savings_rate = None
            profile.positive_factors = ["Financial account active in DhanSarthi."]
            profile.risk_factors = ["At least 3 months of financial records required for creditworthiness evaluation."]
            profile.dimension_scores = {}
            profile.data_coverage = {
                "months_available": months_available,
                "months_required_for_high_confidence": 6,
                "domains_active_count": active_domains_count,
                "total_domains_count": 6,
                "oldest_record": oldest_rec.isoformat() if oldest_rec else None,
                "newest_record": newest_rec.isoformat() if newest_rec else None,
                "income_months": len(income_months_set),
                "expense_months": len(expense_months_set),
                "transaction_months": len(txn_months_set),
                "loan_history_available": loan_history_available,
                "document_evidence_available": has_verified_doc,
                "confidence_score": 0.0,
                "confidence_label": "LOW",
            }
            profile.last_calculated_at = datetime.now(timezone.utc)

            self.db.commit()
            self.db.refresh(profile)
            return profile

        # 3. Dimension Evaluations
        dim_repayment, pos_rep, risk_rep = self._eval_repayment_behaviour(loans, transactions)
        dim_debt, dti_val, pos_debt, risk_debt = self._eval_debt_burden(incomes, loans, liabilities)
        dim_cashflow, margin_val, pos_cf, risk_cf = self._eval_cash_flow_health(incomes, expenses)
        dim_stability, pos_stab, risk_stab = self._eval_income_stability(incomes, documents)
        dim_savings, sav_rate_val, pos_sav, risk_sav = self._eval_savings_liquidity(incomes, expenses, assets, investments)
        dim_discipline, pos_disc, risk_disc = self._eval_budget_discipline(expenses, budgets)

        # 4. Total Score Calculation
        dimensions: Dict[str, CreditDimensionScore] = {
            "repayment_behaviour": dim_repayment,
            "debt_burden": dim_debt,
            "cash_flow_health": dim_cashflow,
            "income_stability": dim_stability,
            "savings_liquidity": dim_savings,
            "budget_discipline": dim_discipline,
        }

        total_score_raw = sum(dim.weighted_score for dim in dimensions.values())
        final_score = int(round(max(0.0, min(100.0, total_score_raw))))

        # 5. Confidence Score Strategy (Separate from numerical score)
        month_conf = min(1.0, months_available / 6.0)
        domain_conf = min(1.0, active_domains_count / 5.0)
        doc_conf = 0.2 if has_verified_doc else 0.0
        confidence_val = round(min(1.0, 0.4 * month_conf + 0.4 * domain_conf + doc_conf), 2)

        if confidence_val >= 0.80:
            conf_label = CreditConfidenceLevel.HIGH
        elif confidence_val >= 0.50:
            conf_label = CreditConfidenceLevel.MEDIUM
        else:
            conf_label = CreditConfidenceLevel.LOW

        # 6. Risk Band Classification
        if final_score >= 80:
            risk_band = RiskBand.STRONG
        elif final_score >= 65:
            risk_band = RiskBand.GOOD
        elif final_score >= 50:
            risk_band = RiskBand.MODERATE
        elif final_score >= 35:
            risk_band = RiskBand.HIGH_RISK
        else:
            risk_band = RiskBand.VERY_HIGH_RISK

        # 7. Loan Readiness State
        if any(getattr(l, "status", None) == LoanStatus.DEFAULTED for l in loans):
            readiness = LoanReadinessState.HIGH_RISK
        elif final_score >= 75 and confidence_val >= 0.50 and (dti_val is None or dti_val <= 0.40):
            readiness = LoanReadinessState.READY
        elif final_score >= 60 and confidence_val >= 0.50 and (dti_val is None or dti_val <= 0.50):
            readiness = LoanReadinessState.NEARLY_READY
        elif final_score >= 60 and confidence_val < 0.50:
            readiness = LoanReadinessState.BUILD_HISTORY
        elif final_score < 50 or (dti_val is not None and dti_val > 0.60):
            readiness = LoanReadinessState.HIGH_RISK
        else:
            readiness = LoanReadinessState.NEARLY_READY

        # Aggregate factors
        all_positive = pos_rep + pos_debt + pos_cf + pos_stab + pos_sav + pos_disc
        all_risk = risk_rep + risk_debt + risk_cf + risk_stab + risk_sav + risk_disc

        # Deduplicate factors while preserving order
        unique_positives = list(dict.fromkeys(all_positive))
        unique_risks = list(dict.fromkeys(all_risk))

        # 8. Update Profile in DB
        profile = (
            self.db.query(CreditProfile)
            .filter(CreditProfile.user_id == user_id)
            .first()
        )
        if not profile:
            profile = CreditProfile(user_id=user_id)
            self.db.add(profile)

        profile.creditworthiness_score = final_score
        profile.status = CreditStatus.CALCULATED
        profile.risk_band = risk_band
        profile.loan_readiness = readiness
        profile.confidence_score = confidence_val
        profile.confidence_label = conf_label
        profile.months_available = months_available
        profile.dti_ratio = round(dti_val, 4) if dti_val is not None else None
        profile.savings_rate = round(sav_rate_val, 2) if sav_rate_val is not None else None
        profile.positive_factors = unique_positives
        profile.risk_factors = unique_risks
        profile.dimension_scores = {k: v.model_dump() for k, v in dimensions.items()}
        profile.data_coverage = {
            "months_available": months_available,
            "months_required_for_high_confidence": 6,
            "domains_active_count": active_domains_count,
            "total_domains_count": 6,
            "oldest_record": oldest_rec.isoformat() if oldest_rec else None,
            "newest_record": newest_rec.isoformat() if newest_rec else None,
            "income_months": len(income_months_set),
            "expense_months": len(expense_months_set),
            "transaction_months": len(txn_months_set),
            "loan_history_available": loan_history_available,
            "document_evidence_available": has_verified_doc,
            "confidence_score": confidence_val,
            "confidence_label": conf_label.value,
        }
        profile.last_calculated_at = datetime.now(timezone.utc)

        # 9. Record Snapshot (One snapshot per day maximum)
        today = date.today()
        existing_snapshot = (
            self.db.query(CreditScoreSnapshot)
            .filter(CreditScoreSnapshot.user_id == user_id, CreditScoreSnapshot.snapshot_date == today)
            .first()
        )
        if not existing_snapshot:
            snapshot = CreditScoreSnapshot(
                user_id=user_id,
                snapshot_date=today,
                score=final_score,
                status=CreditStatus.CALCULATED,
                risk_band=risk_band,
                loan_readiness=readiness,
                confidence_score=confidence_val,
                dimension_scores={k: v.model_dump() for k, v in dimensions.items()},
            )
            self.db.add(snapshot)
        else:
            existing_snapshot.score = final_score
            existing_snapshot.risk_band = risk_band
            existing_snapshot.loan_readiness = readiness
            existing_snapshot.confidence_score = confidence_val
            existing_snapshot.dimension_scores = {k: v.model_dump() for k, v in dimensions.items()}

        self.db.commit()
        self.db.refresh(profile)
        return profile

    def get_score_history(self, user_id: int, limit: int = 12) -> List[CreditScoreSnapshot]:
        """Fetch historical snapshots ordered chronologically for authenticated user."""
        return (
            self.db.query(CreditScoreSnapshot)
            .filter(CreditScoreSnapshot.user_id == user_id)
            .order_by(CreditScoreSnapshot.snapshot_date.asc())
            .limit(limit)
            .all()
        )

    def record_share_consent(self, user_id: int, recipient_name: str) -> CreditShareConsent:
        """Record explicit user consent to share financial creditworthiness profile."""
        consent = CreditShareConsent(
            user_id=user_id,
            recipient_name=recipient_name,
            consent_granted=True,
            consented_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        self.db.add(consent)
        self.db.commit()
        self.db.refresh(consent)
        return consent

    def is_profile_stale(self, profile: CreditProfile) -> bool:
        """Determine whether profile calculation is stale relative to underlying data updates."""
        if not profile or not profile.last_calculated_at:
            return True
        last_calc = profile.last_calculated_at
        if last_calc.tzinfo is None:
            last_calc = last_calc.replace(tzinfo=timezone.utc)

        now_utc = datetime.now(timezone.utc)
        if (now_utc - last_calc) > timedelta(hours=24):
            return True

        user_id = profile.user_id
        latest_timestamps = []

        for model in (Income, Expense, Loan, Liability, Asset, Investment, Budget, Transaction):
            latest_rec = (
                self.db.query(model)
                .filter(model.user_id == user_id)
                .order_by(model.id.desc())
                .first()
            )
            if latest_rec and hasattr(latest_rec, "created_at") and latest_rec.created_at:
                rec_dt = latest_rec.created_at
                if rec_dt.tzinfo is None:
                    rec_dt = rec_dt.replace(tzinfo=timezone.utc)
                latest_timestamps.append(rec_dt)

        if latest_timestamps and max(latest_timestamps) > last_calc:
            return True

        return False

    def get_action_recommendations(self, profile: CreditProfile) -> List[str]:
        """Generate structured, deterministic action recommendations based on weak dimensions."""
        if not profile or profile.status == CreditStatus.INSUFFICIENT_DATA:
            return [
                "Continue recording income, expenses, and transactions to build at least 3 months of verified financial history.",
                "Upload supporting financial documents (e.g., salary slip or tax statement) to substantiate income."
            ]

        recommendations = []
        dti = profile.dti_ratio
        dims = profile.dimension_scores or {}

        if dti is not None and dti > 0.40:
            recommendations.append("Reducing monthly debt obligations could improve your debt-burden assessment.")

        cashflow_dim = dims.get("cash_flow_health") or {}
        if isinstance(cashflow_dim, dict) and cashflow_dim.get("score", 100) < 60:
            recommendations.append("Your recent expenses exceed or tightly balance reported income. Improving monthly surplus may strengthen your assessment.")

        budget_dim = dims.get("budget_discipline") or {}
        if isinstance(budget_dim, dict) and (budget_dim.get("status") == "NOT_CONFIGURED" or budget_dim.get("score", 100) < 70):
            recommendations.append("Create or adhere to monthly category budgets so DhanSarthi can evaluate budget discipline.")

        stability_dim = dims.get("income_stability") or {}
        if isinstance(stability_dim, dict) and stability_dim.get("score", 100) < 70:
            recommendations.append("Your reported income varies significantly across the available period or lacks verified document evidence.")

        liquidity_dim = dims.get("savings_liquidity") or {}
        if isinstance(liquidity_dim, dict) and liquidity_dim.get("score", 100) < 70:
            recommendations.append("Build emergency liquid reserves covering at least 3–6 months of living expenses.")

        if profile.months_available < 6:
            recommendations.append("Continue recording regular income and expense logs to establish a 6+ month history for higher confidence.")

        if not recommendations:
            recommendations.append("Maintain current positive repayment habits, low leverage, and active monthly surplus to sustain your creditworthiness.")

        return recommendations

    def get_score_comparison(self, user_id: int) -> Dict[str, Any]:
        """Compare the two most recent historical DCS snapshots to explain score changes."""
        snapshots = (
            self.db.query(CreditScoreSnapshot)
            .filter(CreditScoreSnapshot.user_id == user_id)
            .order_by(CreditScoreSnapshot.snapshot_date.desc(), CreditScoreSnapshot.created_at.desc())
            .limit(2)
            .all()
        )
        if len(snapshots) < 2:
            return {
                "user_id": user_id,
                "has_comparison": False,
                "previous_score": None,
                "current_score": snapshots[0].score if snapshots else None,
                "score_delta": None,
                "previous_date": None,
                "current_date": snapshots[0].snapshot_date if snapshots else None,
                "dimension_changes": {},
                "explanation_summary": "Insufficient snapshot history for comparison. At least two snapshots are required.",
            }

        curr, prev = snapshots[0], snapshots[1]
        c_score = curr.score or 0
        p_score = prev.score or 0
        delta = c_score - p_score

        dim_changes: Dict[str, float] = {}
        curr_dims = curr.dimension_scores or {}
        prev_dims = prev.dimension_scores or {}

        for k in set(curr_dims.keys()) | set(prev_dims.keys()):
            c_val = curr_dims.get(k, {}).get("weighted_score", 0.0) if isinstance(curr_dims.get(k), dict) else 0.0
            p_val = prev_dims.get(k, {}).get("weighted_score", 0.0) if isinstance(prev_dims.get(k), dict) else 0.0
            dim_changes[k] = round(c_val - p_val, 2)

        if delta > 0:
            summary = f"Your score improved by {delta} points from {p_score} to {c_score}."
        elif delta < 0:
            summary = f"Your score changed by {delta} points from {p_score} to {c_score}."
        else:
            summary = f"Your score remained unchanged at {c_score}."

        return {
            "user_id": user_id,
            "has_comparison": True,
            "previous_score": p_score,
            "current_score": c_score,
            "score_delta": delta,
            "previous_date": prev.snapshot_date,
            "current_date": curr.snapshot_date,
            "dimension_changes": dim_changes,
            "explanation_summary": summary,
        }

    def generate_shareable_profile_report(self, user_id: int) -> Dict[str, Any]:
        """Generate structured creditworthiness report for prospective lender sharing."""
        profile = self.get_or_calculate_credit_profile(user_id)
        incomes = self.db.query(Income).filter(Income.user_id == user_id).all()
        expenses = self.db.query(Expense).filter(Expense.user_id == user_id).all()
        loans = self.db.query(Loan).filter(Loan.user_id == user_id).all()
        assets = self.db.query(Asset).filter(Asset.user_id == user_id).all()

        tot_inc = sum(float(i.amount) for i in incomes)
        tot_exp = sum(float(e.amount) for e in expenses)
        tot_loan = sum(float(getattr(l, "principal_amount", 0.0) or 0.0) for l in loans if getattr(l, "status", None) == LoanStatus.ACTIVE)
        tot_asset = sum(float(getattr(a, "value", 0.0) or 0.0) for a in assets)

        repay_dim = (profile.dimension_scores or {}).get("repayment_behaviour", {})

        return {
            "user_id": user_id,
            "generated_at": datetime.now(timezone.utc),
            "creditworthiness_score": profile.creditworthiness_score,
            "status": profile.status,
            "risk_band": profile.risk_band,
            "confidence_label": profile.confidence_label,
            "loan_readiness": profile.loan_readiness,
            "months_available": profile.months_available,
            "dti_ratio": profile.dti_ratio,
            "savings_rate": profile.savings_rate,
            "positive_factors": profile.positive_factors or [],
            "risk_factors": profile.risk_factors or [],
            "action_recommendations": self.get_action_recommendations(profile),
            "financial_summary": {
                "total_recorded_income": round(tot_inc, 2),
                "total_recorded_expenses": round(tot_exp, 2),
                "total_active_loan_principal": round(tot_loan, 2),
                "total_recorded_assets": round(tot_asset, 2),
            },
            "repayment_indicators": {
                "repayment_behaviour_score": repay_dim.get("score") if isinstance(repay_dim, dict) else None,
                "clean_repayment_record": not any(getattr(l, "status", None) == LoanStatus.DEFAULTED for l in loans),
            },
            "data_coverage": profile.data_coverage or {},
            "disclaimer": "This is DhanSarthi's internal creditworthiness assessment. It is not a CIBIL score, credit bureau score, or guarantee of loan approval.",
        }

    # ------------------------------------------------------------------
    # Private Evaluation Helper Methods
    # ------------------------------------------------------------------

    def _eval_repayment_behaviour(self, loans: List[Loan], transactions: List[Transaction]) -> Tuple[CreditDimensionScore, List[str], List[str]]:
        positives, risks = [], []

        if not loans and not transactions:
            dim = CreditDimensionScore(
                name="repayment_behaviour",
                label="Repayment Behaviour",
                weight=0.25,
                score=50.0,
                weighted_score=12.5,
                description="Evaluates past loan default history and transaction execution reliability.",
                status=CreditDimensionStatus.UNAVAILABLE,
                explanation="No loan repayment history or transaction records available to evaluate payment behavior.",
            )
            risks.append("Repayment history unavailable.")
            return dim, positives, risks

        base_score = 100.0

        # Check for defaulted loans
        defaulted_loans = [l for l in loans if getattr(l, "status", None) == LoanStatus.DEFAULTED]
        if defaulted_loans:
            base_score -= len(defaulted_loans) * 50.0
            risks.append(f"Recorded default on {len(defaulted_loans)} loan obligation(s).")
        else:
            if loans:
                positives.append("Clean loan repayment record with zero defaults.")

        # Check for failed or reversed transactions
        failed_txns = [t for t in transactions if getattr(t, "status", None) in ("FAILED", "REVERSED")]
        if failed_txns:
            penalty = len(failed_txns) * 10.0
            base_score -= penalty
            risks.append(f"{len(failed_txns)} failed or reversed transaction(s) detected.")
        else:
            if transactions:
                positives.append("Flawless transaction execution consistency.")

        score = max(0.0, min(100.0, base_score))
        weighted = score * 0.25

        explanation = (
            f"Evaluated from {len(loans)} loan record(s) and {len(transactions)} transaction(s)."
        )

        dim = CreditDimensionScore(
            name="repayment_behaviour",
            label="Repayment Behaviour",
            weight=0.25,
            score=round(score, 1),
            weighted_score=round(weighted, 1),
            description="Evaluates past loan default history and transaction execution reliability.",
            status=CreditDimensionStatus.AVAILABLE,
            explanation=explanation,
        )
        return dim, positives, risks

    def _eval_debt_burden(self, incomes: List[Income], loans: List[Loan], liabilities: List[Liability]) -> Tuple[CreditDimensionScore, Optional[float], List[str], List[str]]:
        positives, risks = [], []

        tot_income = sum(float(i.amount) for i in incomes)
        tot_emi = sum(
            float(getattr(l, "emi", None) or getattr(l, "emi_amount", None) or 0.0)
            for l in loans if getattr(l, "status", None) == LoanStatus.ACTIVE
        )
        tot_liab_pay = sum(float(lb.monthly_payment) for lb in liabilities if lb.monthly_payment)

        monthly_obligations = tot_emi + tot_liab_pay

        income_months = len({i.income_date.month for i in incomes if i.income_date}) or 1
        monthly_income = tot_income / max(1.0, float(income_months))

        if monthly_income <= 0:
            dti = 1.0 if monthly_obligations > 0 else None
            score = 30.0 if monthly_obligations > 0 else 70.0
            if monthly_obligations > 0:
                risks.append("No active monthly income to service debt obligations.")
            else:
                positives.append("No active recurring debt obligations.")
            explanation = "No reported monthly income available for DTI calculation."
        else:
            dti = monthly_obligations / monthly_income
            if dti <= 0.20:
                score = 100.0
                positives.append(f"Low debt-to-income ratio ({dti * 100:.1f}%). High borrowing capacity.")
            elif dti <= 0.40:
                score = 85.0 - ((dti - 0.20) / 0.20) * 20.0
                positives.append(f"Manageable debt obligations ({dti * 100:.1f}% DTI).")
            elif dti <= 0.60:
                score = 65.0 - ((dti - 0.40) / 0.20) * 35.0
                risks.append(f"Elevated debt-to-income ratio ({dti * 100:.1f}%). High monthly EMI burden.")
            else:
                score = max(0.0, 30.0 - ((dti - 0.60) * 50.0))
                risks.append(f"Critical debt burden ({dti * 100:.1f}% DTI). Exceeds recommended 50% limit.")

            explanation = f"DTI ratio is {dti * 100:.1f}% based on monthly obligations of {monthly_obligations:,.0f} INR."

        weighted = score * 0.20
        dim = CreditDimensionScore(
            name="debt_burden",
            label="Debt Burden & Leverage",
            weight=0.20,
            score=round(score, 1),
            weighted_score=round(weighted, 1),
            description="Measures total recurring debt obligations relative to verified income (DTI).",
            status=CreditDimensionStatus.AVAILABLE,
            explanation=explanation,
        )
        return dim, dti, positives, risks

    def _eval_cash_flow_health(self, incomes: List[Income], expenses: List[Expense]) -> Tuple[CreditDimensionScore, float, List[str], List[str]]:
        positives, risks = [], []

        tot_inc = sum(float(i.amount) for i in incomes)
        tot_exp = sum(float(e.amount) for e in expenses)

        net_surplus = tot_inc - tot_exp
        margin = (net_surplus / tot_inc) if tot_inc > 0 else -1.0

        if tot_inc == 0:
            score = 20.0
            risks.append("No cash inflows recorded in the evaluation window.")
            explanation = "Zero cash inflows recorded."
        elif margin >= 0.30:
            score = 100.0
            positives.append(f"Strong cash flow surplus margin ({margin * 100:.1f}%).")
            explanation = f"Surplus margin of {margin * 100:.1f}% observed."
        elif margin >= 0.10:
            score = 70.0 + ((margin - 0.10) / 0.20) * 30.0
            positives.append(f"Positive net cash flow margin ({margin * 100:.1f}%).")
            explanation = f"Net surplus margin of {margin * 100:.1f}% observed."
        elif margin >= 0.0:
            score = 50.0 + (margin / 0.10) * 20.0
            positives.append("Positive cash flow, but tight surplus margin.")
            explanation = f"Tight surplus margin of {margin * 100:.1f}% observed."
        else:
            score = max(0.0, 50.0 + (margin * 100.0))
            risks.append(f"Negative net cash flow. Outflows exceed income by {abs(net_surplus):,.0f} INR.")
            explanation = f"Negative cash flow margin of {margin * 100:.1f}% observed."

        weighted = score * 0.20
        dim = CreditDimensionScore(
            name="cash_flow_health",
            label="Cash Flow Health",
            weight=0.20,
            score=round(score, 1),
            weighted_score=round(weighted, 1),
            description="Evaluates net monthly surplus margin (Income vs Expenses).",
            status=CreditDimensionStatus.AVAILABLE,
            explanation=explanation,
        )
        return dim, margin, positives, risks

    def _eval_income_stability(self, incomes: List[Income], documents: List[FinancialDocument]) -> Tuple[CreditDimensionScore, List[str], List[str]]:
        positives, risks = [], []

        if not incomes:
            dim = CreditDimensionScore(
                name="income_stability",
                label="Income Stability & Verification",
                weight=0.15,
                score=0.0,
                weighted_score=0.0,
                description="Measures consistency of monthly income and verified document status.",
                status=CreditDimensionStatus.UNAVAILABLE,
                explanation="No income records found inside DhanSarthi.",
            )
            risks.append("No income records found.")
            return dim, positives, risks

        # Group by month
        monthly_map: Dict[Tuple[int, int], float] = {}
        for i in incomes:
            if i.income_date:
                key = (i.income_date.year, i.income_date.month)
                monthly_map[key] = monthly_map.get(key, 0.0) + float(i.amount)

        values = list(monthly_map.values())
        if len(values) > 1:
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            std_dev = math.sqrt(variance)
            cv = (std_dev / mean) if mean > 0 else 1.0

            stability_base = max(20.0, 100.0 - (cv * 100.0))
            if cv < 0.25:
                positives.append("Highly stable month-to-month income flow.")
            else:
                risks.append("Higher variance in month-to-month income streams.")
        else:
            stability_base = 70.0
            positives.append("Income recorded for active period.")

        # Verified document bonus
        has_verified_doc = any(
            doc.document_type in (DocumentType.SALARY_SLIP, DocumentType.TAX_DOCUMENT, DocumentType.BUSINESS_FINANCIAL_DOCUMENT)
            and doc.status in (DocumentStatus.CONFIRMED, DocumentStatus.EXTRACTED)
            for doc in documents
        )

        doc_bonus = 25.0 if has_verified_doc else 0.0
        if has_verified_doc:
            positives.append("Income verified via uploaded salary slip or tax document.")
        else:
            risks.append("No verified salary slip or tax document uploaded to substantiate income.")

        final_score = max(0.0, min(100.0, stability_base * 0.75 + doc_bonus))
        weighted = final_score * 0.15

        explanation = f"Evaluated across {len(values)} month(s) of income history."

        dim = CreditDimensionScore(
            name="income_stability",
            label="Income Stability & Verification",
            weight=0.15,
            score=round(final_score, 1),
            weighted_score=round(weighted, 1),
            description="Measures consistency of monthly income and verified document status.",
            status=CreditDimensionStatus.AVAILABLE,
            explanation=explanation,
        )
        return dim, positives, risks

    def _eval_savings_liquidity(self, incomes: List[Income], expenses: List[Expense], assets: List[Asset], investments: List[Investment]) -> Tuple[CreditDimensionScore, Optional[float], List[str], List[str]]:
        positives, risks = [], []

        tot_inc = sum(float(i.amount) for i in incomes)
        tot_exp = sum(float(e.amount) for e in expenses)

        exp_months = len({e.expense_date.month for e in expenses if e.expense_date}) or 1
        monthly_exp = tot_exp / max(1.0, float(exp_months))

        # Savings rate
        surplus = tot_inc - tot_exp
        savings_rate = (surplus / tot_inc * 100.0) if tot_inc > 0 else 0.0

        # Liquid assets (Cash + Liquid holdings)
        def _get_val(obj: Any) -> float:
            v = getattr(obj, "value", None)
            if v is None:
                v = getattr(obj, "current_value", 0.0)
            return float(v)

        def _is_liquid_asset(a: Any) -> bool:
            if getattr(a, "is_liquid", False):
                return True
            atype = str(getattr(a, "asset_type", "")).upper()
            return any(k in atype for k in ("CASH", "BANK", "GOLD", "STOCK"))

        liquid_assets = sum(_get_val(a) for a in assets if _is_liquid_asset(a))
        investment_val = sum(_get_val(inv) for inv in investments)
        total_reserve = liquid_assets + (investment_val * 0.5)

        months_reserve = (total_reserve / monthly_exp) if monthly_exp > 0 else (5.0 if total_reserve > 0 else 0.0)

        if savings_rate >= 20.0:
            positives.append(f"Healthy monthly savings rate ({savings_rate:.1f}%).")
        elif savings_rate < 5.0 and tot_inc > 0:
            risks.append(f"Low savings rate ({savings_rate:.1f}%). Limited accumulation.")

        if months_reserve >= 6.0:
            score = 100.0
            positives.append(f"Robust liquidity reserve covering {months_reserve:.1f} months of expenses.")
        elif months_reserve >= 3.0:
            score = 70.0 + ((months_reserve - 3.0) / 3.0) * 30.0
            positives.append(f"Adequate liquid reserve covering {months_reserve:.1f} months of expenses.")
        elif months_reserve > 0:
            score = 30.0 + (months_reserve / 3.0) * 40.0
            risks.append(f"Liquid reserve covers only {months_reserve:.1f} months of expenses (6 months recommended).")
        else:
            score = 10.0
            risks.append("No liquid emergency reserves recorded.")

        explanation = f"Liquid reserves cover {months_reserve:.1f} month(s) of estimated living expenses."

        weighted = score * 0.10
        dim = CreditDimensionScore(
            name="savings_liquidity",
            label="Savings & Liquidity Strength",
            weight=0.10,
            score=round(score, 1),
            weighted_score=round(weighted, 1),
            description="Measures emergency liquid buffer (Months of expenses covered).",
            status=CreditDimensionStatus.AVAILABLE,
            explanation=explanation,
        )
        return dim, savings_rate, positives, risks

    def _eval_budget_discipline(self, expenses: List[Expense], budgets: List[Budget]) -> Tuple[CreditDimensionScore, List[str], List[str]]:
        positives, risks = [], []

        if not budgets:
            dim = CreditDimensionScore(
                name="budget_discipline",
                label="Budget & Expense Discipline",
                weight=0.10,
                score=75.0,
                weighted_score=7.5,
                description="Evaluates adherence to user-defined monthly category budgets.",
                status=CreditDimensionStatus.NOT_CONFIGURED,
                explanation="No active category budgets configured. Baseline neutral assessment applied.",
            )
            risks.append("No category budgets configured.")
            return dim, positives, risks

        # Calculate actual category spending
        cat_spending: Dict[str, float] = {}
        for e in expenses:
            cat = (e.category or "Other").lower()
            cat_spending[cat] = cat_spending.get(cat, 0.0) + float(e.amount)

        within_limit = 0
        total_budgets = len(budgets)

        for b in budgets:
            b_cat = (b.category or "Other").lower()
            limit = float(b.monthly_limit)
            actual = cat_spending.get(b_cat, 0.0)
            if actual <= limit:
                within_limit += 1

        ratio = within_limit / total_budgets
        score = ratio * 100.0

        if ratio == 1.0:
            positives.append("100% budget adherence across all category limits.")
        elif ratio >= 0.70:
            positives.append(f"Good budget discipline ({within_limit}/{total_budgets} categories within budget).")
        else:
            risks.append(f"Budget overruns detected in {total_budgets - within_limit} of {total_budgets} configured categories.")

        explanation = f"Budget adherence at {within_limit}/{total_budgets} configured categories."

        weighted = score * 0.10
        dim = CreditDimensionScore(
            name="budget_discipline",
            label="Budget & Expense Discipline",
            weight=0.10,
            score=round(score, 1),
            weighted_score=round(weighted, 1),
            description="Evaluates adherence to user-defined monthly category budgets.",
            status=CreditDimensionStatus.AVAILABLE,
            explanation=explanation,
        )
        return dim, positives, risks
