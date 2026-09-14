"""Investment Guide Core Analytical Engine.

Implements deterministic opportunity scoring, demand scoring, personalized asset allocation,
investment tree generation, and portfolio health integration.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.market_data.schemas import StockQuote, IndexQuote, MutualFundNAV
from app.market_data.service import MarketDataService
from app.models.enums import InvestmentType
from app.models.investment import Investment
from app.schemas.investment_guide import (
    MarketIndexOverview,
    MarketOverviewResponse,
    OpportunityCard,
    OpportunityScoreDetails,
    TechnicalIndicatorsResponse,
    InvestmentPlanRequest,
    InvestmentPlanResponse,
    InvestmentTreeNode,
    PortfolioAnalysisResponse,
    MarketStatusResponse,
)

# Benchmark asset universe catalog for Opportunity Scanner
SUPPORTED_ASSET_UNIVERSE = [
    {"id": "RELIANCE", "symbol": "RELIANCE.NS", "name": "Reliance Industries Ltd.", "category": "Stocks", "base_price": 2850.50, "risk": "Moderate", "horizon": "3-5 years", "sector": "Energy"},
    {"id": "TCS", "symbol": "TCS.NS", "name": "Tata Consultancy Services", "category": "Stocks", "base_price": 3950.00, "risk": "Moderate", "horizon": "3-5 years", "sector": "Technology"},
    {"id": "INFY", "symbol": "INFY.NS", "name": "Infosys Ltd.", "category": "Stocks", "base_price": 1780.20, "risk": "Moderate", "horizon": "3-5 years", "sector": "Technology"},
    {"id": "HDFCBANK", "symbol": "HDFCBANK.NS", "name": "HDFC Bank Ltd.", "category": "Stocks", "base_price": 1620.00, "risk": "Moderate", "horizon": "3-5 years", "sector": "Banking"},
    {"id": "ICICIBANK", "symbol": "ICICIBANK.NS", "name": "ICICI Bank Ltd.", "category": "Stocks", "base_price": 1150.80, "risk": "Moderate", "horizon": "3-5 years", "sector": "Banking"},
    {"id": "TATAMOTORS", "symbol": "TATAMOTORS.NS", "name": "Tata Motors Ltd.", "category": "Stocks", "base_price": 980.40, "risk": "High", "horizon": "3-5 years", "sector": "Auto"},
    
    {"id": "MF_SBI_BLUECHIP", "symbol": "119063", "name": "SBI Bluechip Fund - Direct Growth", "category": "Mutual Funds", "base_price": 128.40, "risk": "Moderate", "horizon": "3-5 years", "sector": "Large Cap Equity"},
    {"id": "MF_HDFC_TOP100", "symbol": "102873", "name": "HDFC Top 100 Fund - Growth", "category": "Mutual Funds", "base_price": 315.60, "risk": "Moderate", "horizon": "3-5 years", "sector": "Large Cap Equity"},
    {"id": "MF_NIPPON_SMALLCAP", "symbol": "118989", "name": "Nippon India Small Cap Fund", "category": "Mutual Funds", "base_price": 165.20, "risk": "High", "horizon": "5+ years", "sector": "Small Cap Equity"},
    
    {"id": "ETF_NIFTY50", "symbol": "NIFTYBEES.NS", "name": "Nippon India ETF Nifty 50 BeES", "category": "ETFs", "base_price": 245.50, "risk": "Low", "horizon": "3-5 years", "sector": "Index ETF"},
    {"id": "ETF_BANK", "symbol": "BANKBEES.NS", "name": "Nippon India ETF Bank BeES", "category": "ETFs", "base_price": 510.30, "risk": "Moderate", "horizon": "3-5 years", "sector": "Banking ETF"},
    
    {"id": "GOLD_DIGITAL", "symbol": "GOLD_DIGITAL", "name": "Sovereign / Digital Gold BeES", "category": "Gold", "base_price": 7250.00, "risk": "Low", "horizon": "3-5 years", "sector": "Commodity"},
    {"id": "BONDS_GOI_775", "symbol": "GOI775_2034", "name": "Govt of India 7.75% 10Y Bond", "category": "Bonds", "base_price": 102.50, "risk": "Low", "horizon": "5+ years", "sector": "Sovereign Debt"},
    {"id": "TBILLS_364D", "symbol": "TBILL364", "name": "RBI 364-Day Treasury Bill", "category": "T-Bills", "base_price": 93.50, "risk": "Low", "horizon": "<1 year", "sector": "Govt Money Market"},
    {"id": "FD_HDFC_1Y", "symbol": "FD_HDFC_1Y", "name": "HDFC Bank Fixed Deposit (7.25%)", "category": "FD/RD", "base_price": 1000.00, "risk": "Low", "horizon": "1-3 years", "sector": "Banking Deposit"},
    {"id": "CRYPTO_BTC", "symbol": "BTC", "name": "Bitcoin (High Risk Benchmark)", "category": "Crypto", "base_price": 54000.00, "risk": "Very High", "horizon": "5+ years", "sector": "Digital Assets"},
]


class OpportunityScoringEngine:
    """
    Deterministic scoring engine calculating scores based on price momentum,
    trend, volume ratios, and fundamentals.
    """

    @staticmethod
    def calculate_scores(
        change_pct: float,
        price: float,
        category: str,
        symbol: str,
        volume_ratio: float = 1.15,
        rsi: float = 58.0,
        pe_ratio: Optional[float] = None
    ) -> Tuple[OpportunityScoreDetails, str, str]:
        """
        Returns (OpportunityScoreDetails, demand_rationale, score_explanation).
        """
        signals: List[str] = []
        unavailable: List[str] = []

        # 1. Momentum Score (0-100)
        # Positive price change and strong RSI contribute positively
        rsi_factor = max(0.0, min(100.0, rsi))
        if change_pct > 0:
            momentum = min(95.0, 50.0 + (change_pct * 8.0) + (rsi_factor - 50.0) * 0.4)
            signals.append("positive_price_momentum")
        else:
            momentum = max(10.0, 50.0 + (change_pct * 8.0) + (rsi_factor - 50.0) * 0.4)
            signals.append("short_term_price_consolidation")

        # 2. Demand Score (0-100)
        # Volume ratio > 1.0 indicates above-average volume activity
        if volume_ratio >= 1.2:
            demand = min(95.0, 60.0 + (volume_ratio - 1.0) * 30.0)
            demand_rationale = f"Trading volume is {(volume_ratio - 1.0)*100:.1f}% above the 20-day baseline average."
            signals.append("elevated_trading_volume")
        elif volume_ratio >= 0.9:
            demand = 65.0
            demand_rationale = "Trading volume and market liquidity are aligned with recent historical averages."
            signals.append("steady_liquidity")
        else:
            demand = 40.0
            demand_rationale = "Trading activity is lower than the recent 20-day moving average."
            signals.append("subdued_trading_activity")

        # 3. Fundamental Score (0-100)
        if pe_ratio is not None and pe_ratio > 0:
            if pe_ratio < 20.0:
                fundamental = 85.0
                signals.append("attractive_valuation_pe")
            elif pe_ratio < 35.0:
                fundamental = 70.0
                signals.append("fair_market_valuation")
            else:
                fundamental = 50.0
                signals.append("premium_valuation")
        else:
            if category in ["Gold", "T-Bills", "FD/RD", "Bonds"]:
                fundamental = 80.0
                signals.append("sovereign_guarantee_or_fixed_yield")
            else:
                fundamental = 65.0
                unavailable.append("earnings_pe_ratio")

        # 4. Risk-Adjusted Score
        category_risk_penalty = {
            "Stocks": 10.0,
            "Mutual Funds": 5.0,
            "ETFs": 5.0,
            "Gold": 2.0,
            "Bonds": 2.0,
            "T-Bills": 0.0,
            "FD/RD": 0.0,
            "Crypto": 35.0,
        }.get(category, 10.0)

        risk_adjusted = max(10.0, min(95.0, (momentum * 0.4 + demand * 0.3 + fundamental * 0.3) - category_risk_penalty))

        # Overall Opportunity Score
        opportunity = max(10.0, min(98.0, (momentum * 0.35 + demand * 0.25 + fundamental * 0.25 + risk_adjusted * 0.15)))

        # Confidence calculation
        confidence = 0.92 if not unavailable else 0.78

        details = OpportunityScoreDetails(
            opportunity_score=int(round(opportunity)),
            demand_score=int(round(demand)),
            momentum_score=int(round(momentum)),
            fundamental_score=int(round(fundamental)) if fundamental else None,
            risk_adjusted_score=int(round(risk_adjusted)),
            confidence=confidence,
            signals=signals,
            unavailable_metrics=unavailable,
        )

        # Rationale wording (Educational & compliant)
        if opportunity >= 75:
            explanation = f"High opportunity score driven by {signals[0].replace('_', ' ')} and robust demand signals."
        elif opportunity >= 55:
            explanation = f"Balanced market profile with {signals[0].replace('_', ' ')} and steady risk parameters."
        else:
            explanation = f"Moderate opportunity score due to neutral technical signals and elevated risk level."

        return details, demand_rationale, explanation


class InvestmentPlanningEngine:
    """
    Engine for generating personalized asset allocation and dynamic Investment Tree structures.
    """

    @staticmethod
    def generate_plan(req: InvestmentPlanRequest) -> InvestmentPlanResponse:
        amount = float(req.amount)
        monthly_sip = float(req.monthly_sip)
        risk = req.risk_profile.lower()
        horizon = req.horizon

        # Base allocation according to risk profile
        if risk == "conservative":
            eq, debt, gold, liquid, alt = 15.0, 50.0, 15.0, 20.0, 0.0
        elif risk == "aggressive":
            eq, debt, gold, liquid, alt = 65.0, 15.0, 10.0, 5.0, 5.0
        else:  # moderate
            eq, debt, gold, liquid, alt = 45.0, 30.0, 15.0, 10.0, 0.0

        # Adjust based on horizon
        if horizon in ["<1", "<1 year"]:
            # Shift heavily to liquid and short-term debt
            liquid += eq * 0.6
            debt += eq * 0.4
            eq = 0.0
        elif horizon in ["1-3", "1-3 years"]:
            liquid += eq * 0.3
            debt += eq * 0.2
            eq *= 0.5

        # Normalize breakdown to sum to 100%
        total_weight = eq + debt + gold + liquid + alt
        allocation_breakdown = {
            "Equity & Mutual Funds": round((eq / total_weight) * 100, 1),
            "Debt & Bonds": round((debt / total_weight) * 100, 1),
            "Gold & Commodities": round((gold / total_weight) * 100, 1),
            "Liquid & Money Market": round((liquid / total_weight) * 100, 1),
        }
        if alt > 0:
            allocation_breakdown["Alternative / Crypto"] = round((alt / total_weight) * 100, 1)

        # Build Investment Tree
        now_str = datetime.now(timezone.utc).isoformat()
        tree = InvestmentPlanningEngine._build_tree(
            amount=amount,
            monthly_sip=monthly_sip,
            allocation=allocation_breakdown,
            emergency_status=req.emergency_reserve_status or "adequate",
            risk_profile=risk,
            horizon=horizon
        )

        return InvestmentPlanResponse(
            created_at=now_str,
            risk_profile=risk.capitalize(),
            horizon=horizon,
            total_capital=req.amount,
            monthly_sip=req.monthly_sip,
            allocation_breakdown=allocation_breakdown,
            tree_data=tree,
        )

    @staticmethod
    def _build_tree(
        amount: float,
        monthly_sip: float,
        allocation: Dict[str, float],
        emergency_status: str,
        risk_profile: str,
        horizon: str
    ) -> InvestmentTreeNode:
        """
        Builds hierarchical tree structure:
        Investment Plan
        ├── Emergency Reserve (if needed)
        ├── Short Term (<1yr)
        ├── Medium Term (1-3yrs)
        └── Long Term (3-5yrs / 5+yrs)
        """
        tree_children: List[InvestmentTreeNode] = []

        # 1. Emergency Reserve Branch (If not fully adequate)
        if emergency_status in ["none", "partial"]:
            res_pct = 20.0 if emergency_status == "none" else 10.0
            res_amt = (amount * res_pct) / 100.0
            tree_children.append(
                InvestmentTreeNode(
                    name="Emergency Reserve",
                    type="category",
                    allocation_percent=res_pct,
                    amount=Decimal(f"{res_amt:.2f}"),
                    risk_level="Low",
                    expected_horizon="Immediate / Liquid",
                    opportunity_score=85,
                    reason="Maintains financial safety buffer in high-yield liquid funds before risk deployment.",
                    children=[
                        InvestmentTreeNode(
                            name="Liquid Mutual Funds",
                            type="asset",
                            allocation_percent=res_pct * 0.6,
                            amount=Decimal(f"{res_amt * 0.6:.2f}"),
                            risk_level="Low",
                            expected_horizon="Immediate",
                            opportunity_score=88,
                            reason="Instant redemption capability with steady capital preservation.",
                        ),
                        InvestmentTreeNode(
                            name="High-Yield Savings / Bank FD",
                            type="asset",
                            allocation_percent=res_pct * 0.4,
                            amount=Decimal(f"{res_amt * 0.4:.2f}"),
                            risk_level="Low",
                            expected_horizon="Immediate",
                            opportunity_score=82,
                            reason="Guaranteed principal backed by deposit insurance.",
                        ),
                    ]
                )
            )

        # 2. Short-Term Branch (<1 Year)
        st_pct = allocation.get("Liquid & Money Market", 10.0)
        st_amt = (amount * st_pct) / 100.0
        if st_pct > 0:
            tree_children.append(
                InvestmentTreeNode(
                    name="Short Term Investments",
                    type="category",
                    allocation_percent=st_pct,
                    amount=Decimal(f"{st_amt:.2f}"),
                    risk_level="Low",
                    expected_horizon="<1 year",
                    opportunity_score=82,
                    reason="Focuses on liquidity preservation, short duration T-Bills, and RDs.",
                    children=[
                        InvestmentTreeNode(
                            name="RBI Treasury Bills (364D)",
                            type="asset",
                            allocation_percent=round(st_pct * 0.5, 1),
                            amount=Decimal(f"{st_amt * 0.5:.2f}"),
                            risk_level="Low",
                            expected_horizon="<1 year",
                            opportunity_score=85,
                            reason="Zero default risk backed by Reserve Bank of India.",
                        ),
                        InvestmentTreeNode(
                            name="Recurring Deposit (RD) / Short FD",
                            type="asset",
                            allocation_percent=round(st_pct * 0.5, 1),
                            amount=Decimal(f"{st_amt * 0.5:.2f}"),
                            risk_level="Low",
                            expected_horizon="<1 year",
                            opportunity_score=80,
                            reason="Predictable yield accumulation for short-term targets.",
                        ),
                    ]
                )
            )

        # 3. Medium-Term Branch (1–3 Years)
        mt_pct = allocation.get("Debt & Bonds", 25.0)
        mt_amt = (amount * mt_pct) / 100.0
        if mt_pct > 0:
            tree_children.append(
                InvestmentTreeNode(
                    name="Medium Term Growth & Debt",
                    type="category",
                    allocation_percent=mt_pct,
                    amount=Decimal(f"{mt_amt:.2f}"),
                    risk_level="Low to Moderate",
                    expected_horizon="1-3 years",
                    opportunity_score=78,
                    reason="Generates steady coupon yields and inflation-hedged income.",
                    children=[
                        InvestmentTreeNode(
                            name="Government & Corporate Bonds",
                            type="asset",
                            allocation_percent=round(mt_pct * 0.6, 1),
                            amount=Decimal(f"{mt_amt * 0.6:.2f}"),
                            risk_level="Low",
                            expected_horizon="1-3 years",
                            opportunity_score=82,
                            reason="Provides predictable semi-annual coupon payouts.",
                        ),
                        InvestmentTreeNode(
                            name="Conservative Hybrid Debt Funds",
                            type="asset",
                            allocation_percent=round(mt_pct * 0.4, 1),
                            amount=Decimal(f"{mt_amt * 0.4:.2f}"),
                            risk_level="Moderate",
                            expected_horizon="1-3 years",
                            opportunity_score=75,
                            reason="Combines fixed income security with modest equity upside.",
                        ),
                    ]
                )
            )

        # 4. Long-Term Branch (3–5+ Years)
        lt_equity_pct = allocation.get("Equity & Mutual Funds", 45.0)
        lt_gold_pct = allocation.get("Gold & Commodities", 15.0)
        lt_pct = lt_equity_pct + lt_gold_pct
        lt_amt = (amount * lt_pct) / 100.0
        if lt_pct > 0:
            lt_children = [
                InvestmentTreeNode(
                    name="Nifty 50 & Large-Cap Index Funds",
                    type="asset",
                    allocation_percent=round(lt_equity_pct * 0.6, 1),
                    amount=Decimal(f"{(amount * lt_equity_pct * 0.6) / 100.0:.2f}"),
                    risk_level="Moderate",
                    expected_horizon="3-5+ years",
                    opportunity_score=88,
                    reason="Captures top 50 Indian corporate growth with low expense ratio.",
                ),
                InvestmentTreeNode(
                    name="Direct Quality Equity / Flexi-Cap",
                    type="asset",
                    allocation_percent=round(lt_equity_pct * 0.4, 1),
                    amount=Decimal(f"{(amount * lt_equity_pct * 0.4) / 100.0:.2f}"),
                    risk_level="Moderate to High",
                    expected_horizon="5+ years",
                    opportunity_score=84,
                    reason="Targets high compounding capacity across market cycles.",
                ),
                InvestmentTreeNode(
                    name="Sovereign / Digital Gold",
                    type="asset",
                    allocation_percent=round(lt_gold_pct, 1),
                    amount=Decimal(f"{(amount * lt_gold_pct) / 100.0:.2f}"),
                    risk_level="Low",
                    expected_horizon="3-5+ years",
                    opportunity_score=81,
                    reason="Hedges portfolio against inflation and currency devaluation.",
                ),
            ]

            # Optional Crypto / Alt Asset Branch (Never classified as short-term!)
            alt_pct = allocation.get("Alternative / Crypto", 0.0)
            if alt_pct > 0:
                lt_children.append(
                    InvestmentTreeNode(
                        name="High-Risk Tactical Assets (Crypto/Alt)",
                        type="asset",
                        allocation_percent=round(alt_pct, 1),
                        amount=Decimal(f"{(amount * alt_pct) / 100.0:.2f}"),
                        risk_level="Very High",
                        expected_horizon="5+ years (High Risk)",
                        opportunity_score=62,
                        reason="Optional speculative satellite allocation. Strictly isolated from core wealth.",
                    )
                )

            tree_children.append(
                InvestmentTreeNode(
                    name="Long Term Wealth Compounding",
                    type="category",
                    allocation_percent=round(lt_pct + allocation.get("Alternative / Crypto", 0.0), 1),
                    amount=Decimal(f"{lt_amt:.2f}"),
                    risk_level="Moderate to High",
                    expected_horizon="3-5+ years",
                    opportunity_score=86,
                    reason="Maximizes multi-year capital growth via index funds, equities, and gold.",
                    children=lt_children
                )
            )

        return InvestmentTreeNode(
            name="Personalized Investment Strategy Tree",
            type="root",
            allocation_percent=100.0,
            amount=Decimal(f"{amount:.2f}"),
            risk_level=risk_profile.capitalize(),
            expected_horizon=horizon,
            opportunity_score=84,
            reason=f"Structured portfolio strategy customized for a {risk_profile} investor.",
            children=tree_children
        )


class PortfolioGuideAnalysisEngine:
    """
    Engine to analyze user's existing portfolio records from DB and produce health scores.
    """

    @staticmethod
    def analyze_user_portfolio(user_id: int, db: Session) -> PortfolioAnalysisResponse:
        holdings = db.query(Investment).filter(Investment.user_id == user_id).all()

        if not holdings:
            return PortfolioAnalysisResponse(
                total_holdings_value=Decimal("0.00"),
                diversification_score=50,
                concentration_risk="Low",
                liquidity_score=60,
                risk_balance_score=50,
                portfolio_health_score=55,
                asset_allocation={"Unallocated": 100.0},
                growth_exposure_percent=0.0,
                observations=[
                    "No existing holdings found in your portfolio database.",
                    "Use the Personalized Planner to construct your initial investment allocation."
                ]
            )

        total_val = sum((h.current_value for h in holdings), Decimal("0"))
        if total_val == Decimal("0"):
            total_val = Decimal("1.0")  # Avoid divide by zero

        # Group by investment type
        type_totals: Dict[str, Decimal] = {}
        for h in holdings:
            t_str = str(h.investment_type.value if hasattr(h.investment_type, "value") else h.investment_type)
            type_totals[t_str] = type_totals.get(t_str, Decimal("0")) + h.current_value

        allocation: Dict[str, float] = {
            t: float(round((val / total_val) * Decimal("100"), 1))
            for t, val in type_totals.items()
        }

        # Calculate Growth Exposure (Stocks + Mutual Funds + ETFs)
        growth_val = sum((type_totals.get(t, Decimal("0")) for t in ["STOCK", "MUTUAL_FUND", "ETF"]), Decimal("0"))
        growth_pct = float(round((growth_val / total_val) * Decimal("100"), 1))

        # Diversification score based on number of asset classes
        num_classes = len(type_totals)
        div_score = min(100, num_classes * 25)

        # Concentration risk: if single asset class > 50%
        max_class_pct = max(allocation.values()) if allocation else 0.0
        if max_class_pct > 60.0:
            conc_risk = "High"
        elif max_class_pct > 40.0:
            conc_risk = "Moderate"
        else:
            conc_risk = "Low"

        # Health score calculation
        health_score = int(round((div_score * 0.4) + ((100.0 - max_class_pct) * 0.4) + 20.0))
        health_score = max(20, min(95, health_score))

        observations = []
        if max_class_pct > 50.0:
            dominant_class = [k for k, v in allocation.items() if v == max_class_pct][0]
            observations.append(f"Your portfolio has high {dominant_class.lower()} concentration ({max_class_pct}%).")
        if growth_pct < 20.0:
            observations.append("Your equity exposure is below the recommended target range for long-term growth.")
        elif growth_pct > 80.0:
            observations.append("Your equity exposure is high. Consider hedging with gold or short-duration debt.")
        if len(holdings) >= 3:
            observations.append(f"Portfolio contains {len(holdings)} active holdings across {num_classes} asset categories.")

        return PortfolioAnalysisResponse(
            total_holdings_value=total_val,
            diversification_score=div_score,
            concentration_risk=conc_risk,
            liquidity_score=75,
            risk_balance_score=int(round(100.0 - (max_class_pct * 0.5))),
            portfolio_health_score=health_score,
            asset_allocation=allocation,
            growth_exposure_percent=growth_pct,
            observations=observations,
        )
