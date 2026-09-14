"""Pydantic schemas for the Investment Guide endpoints and scoring engines."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MarketIndexOverview(BaseModel):
    """Index overview schema for NIFTY, SENSEX, BANK NIFTY."""

    name: str = Field(..., description="Index name (e.g. NIFTY 50, SENSEX)")
    value: Decimal = Field(..., description="Current index value")
    change: Decimal = Field(default=Decimal("0.00"), description="Absolute daily change")
    change_percent: Decimal = Field(default=Decimal("0.00"), description="Percentage daily change")
    status: str = Field(default="OPEN", description="Market status")


class MarketOverviewResponse(BaseModel):
    """Combined market overview with breadth and volatility metrics."""

    nifty_50: MarketIndexOverview
    sensex: MarketIndexOverview
    bank_nifty: Optional[MarketIndexOverview] = None
    market_direction: str = Field(..., description="Bullish, Bearish, Neutral, Consolidation")
    market_breadth: str = Field(..., description="e.g. 32 Advances / 18 Declines")
    volatility_index: Decimal = Field(..., description="India VIX equivalent index value")
    updated_at: str = Field(..., description="ISO timestamp of last update")
    source: str = Field(..., description="Source of data")
    provider: str = Field(..., description="Provider name")
    is_stale: bool = Field(default=False, description="Whether cache is stale")


class OpportunityScoreDetails(BaseModel):
    """Detailed score breakdown calculated deterministically by scoring engine."""

    opportunity_score: int = Field(..., ge=0, le=100, description="Overall opportunity score 0-100")
    demand_score: int = Field(..., ge=0, le=100, description="Demand score 0-100")
    momentum_score: int = Field(..., ge=0, le=100, description="Momentum score 0-100")
    fundamental_score: Optional[int] = Field(None, ge=0, le=100, description="Fundamental score 0-100 if data available")
    risk_adjusted_score: int = Field(..., ge=0, le=100, description="Risk-adjusted score 0-100")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence metric 0.0-1.0")
    signals: List[str] = Field(default_factory=list, description="List of positive/negative signals")
    unavailable_metrics: List[str] = Field(default_factory=list, description="Metrics omitted due to missing data")


class OpportunityCard(BaseModel):
    """Normalized investment opportunity card schema."""

    id: str = Field(..., description="Unique asset identifier")
    name: str = Field(..., description="Full asset or security name")
    symbol: str = Field(..., description="Ticker symbol or scheme code")
    asset_category: str = Field(..., description="Stocks, Mutual Funds, ETFs, Gold, Bonds, T-Bills, FD/RD, Crypto")
    price: Decimal = Field(..., description="Current price or NAV")
    currency: str = Field(default="INR", description="Quote currency")
    change_percent: Decimal = Field(default=Decimal("0.0"), description="24h / Daily percentage change")
    scores: OpportunityScoreDetails
    demand_rationale: str = Field(..., description="Data-driven demand explanation")
    risk_level: str = Field(..., description="Low, Moderate, High, Very High")
    suggested_horizon: str = Field(..., description="<1 year, 1-3 years, 3-5 years, 5+ years")
    explanation: str = Field(..., description="Brief data-grounded rationale for the assigned scores")
    updated_at: str = Field(..., description="Last update timestamp")
    provider: str = Field(..., description="Provider name")


class TechnicalIndicatorsResponse(BaseModel):
    """Technical and fundamental indicators for a target asset."""

    symbol: str
    price: Decimal
    rsi_14: Optional[float] = Field(None, description="14-period RSI indicator")
    macd_signal: Optional[str] = Field(None, description="Bullish, Bearish, Neutral")
    sma_50: Optional[Decimal] = Field(None, description="50-day Simple Moving Average")
    sma_200: Optional[Decimal] = Field(None, description="200-day Simple Moving Average")
    volume_ratio_20d: Optional[float] = Field(None, description="Current volume relative to 20-day average")
    annualized_volatility: Optional[float] = Field(None, description="Annualized percentage volatility")
    trend: str = Field("UPTREND", description="UPTREND, DOWNTREND, SIDEWAYS")
    fundamentals: Dict[str, Any] = Field(default_factory=dict, description="P/E, P/B, ROE, Debt/Equity where available")
    updated_at: str
    provider: str


class InvestmentPlanRequest(BaseModel):
    """Request payload for personalized investment planner."""

    amount: Decimal = Field(..., gt=0, description="Lump sum investment amount in INR")
    monthly_sip: Decimal = Field(default=Decimal("0"), ge=0, description="Monthly SIP commitment in INR")
    risk_profile: str = Field(default="moderate", description="conservative, moderate, aggressive")
    horizon: str = Field(default="3-5", description="<1, 1-3, 3-5, 5+")
    financial_goal: Optional[str] = Field(default="Wealth Generation", description="Target goal description")
    emergency_reserve_status: Optional[str] = Field(default="adequate", description="adequate, partial, none")
    preferred_assets: List[str] = Field(default_factory=list, description="Filtered preferences")


class InvestmentTreeNode(BaseModel):
    """Hierarchical node structure for Investment Tree visualization."""

    name: str
    type: str = Field(..., description="root, category, subcategory, asset")
    allocation_percent: float = Field(..., ge=0, le=100)
    amount: Decimal
    risk_level: str = Field(..., description="Low, Moderate, High, Very High")
    expected_horizon: str
    opportunity_score: Optional[int] = None
    reason: str
    children: List[InvestmentTreeNode] = Field(default_factory=list)


class InvestmentPlanResponse(BaseModel):
    """Response payload for generated investment plan."""

    plan_id: Optional[int] = None
    created_at: str
    risk_profile: str
    horizon: str
    total_capital: Decimal
    monthly_sip: Decimal
    allocation_breakdown: Dict[str, float]
    tree_data: InvestmentTreeNode
    safety_disclaimer: str = Field(
        default="All allocations and signals are analytical estimates based on market data. Returns are not guaranteed.",
        description="Mandatory educational compliance notice"
    )


class PortfolioAnalysisResponse(BaseModel):
    """Integration response reading user's active holdings."""

    total_holdings_value: Decimal
    diversification_score: int = Field(..., ge=0, le=100)
    concentration_risk: str = Field(..., description="Low, Moderate, High")
    liquidity_score: int = Field(..., ge=0, le=100)
    risk_balance_score: int = Field(..., ge=0, le=100)
    portfolio_health_score: int = Field(..., ge=0, le=100)
    asset_allocation: Dict[str, float]
    growth_exposure_percent: float
    observations: List[str]


class MarketStatusResponse(BaseModel):
    """Overall market status and liquidity overview."""

    market_status: str = Field(..., description="OPEN, CLOSED, PRE_MARKET")
    is_open: bool
    trading_phase: str
    volatility_regime: str = Field(..., description="LOW, NORMAL, ELEVATED, HIGH")
    liquidity_level: str = Field(..., description="HIGH, NORMAL, CONSTRAINED")
    last_check: str
