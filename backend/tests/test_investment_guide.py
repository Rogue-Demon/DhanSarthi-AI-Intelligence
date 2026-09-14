"""Unit test suite for DhanSarthi Investment Guide endpoints, scoring engine, and planning engine."""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.services.investment_guide_engine import (
    OpportunityScoringEngine,
    InvestmentPlanningEngine,
    PortfolioGuideAnalysisEngine,
)
from app.schemas.investment_guide import InvestmentPlanRequest

client = TestClient(app)


def test_scoring_engine_calculation():
    """Validates deterministic scoring engine metrics, confidence, and signals."""
    scores, demand_rat, explanation = OpportunityScoringEngine.calculate_scores(
        change_pct=2.45,
        price=1850.00,
        category="Stocks",
        symbol="RELIANCE.NS",
        volume_ratio=1.35,
        rsi=62.0,
        pe_ratio=22.5
    )

    assert scores.opportunity_score >= 0 and scores.opportunity_score <= 100
    assert scores.demand_score >= 0 and scores.demand_score <= 100
    assert scores.momentum_score >= 0 and scores.momentum_score <= 100
    assert scores.risk_adjusted_score >= 0 and scores.risk_adjusted_score <= 100
    assert scores.confidence >= 0.7
    assert len(scores.signals) > 0
    assert "guaranteed" not in explanation.lower()
    assert "profit" not in explanation.lower()


def test_investment_planner_allocation():
    """Validates personalized planner allocation weights and tree structure."""
    req = InvestmentPlanRequest(
        amount=Decimal("200000.00"),
        monthly_sip=Decimal("15000.00"),
        risk_profile="moderate",
        horizon="3-5",
        financial_goal="Wealth Generation",
        emergency_reserve_status="partial"
    )

    res = InvestmentPlanningEngine.generate_plan(req)

    assert res.total_capital == Decimal("200000.00")
    assert res.risk_profile == "Moderate"
    assert "Equity & Mutual Funds" in res.allocation_breakdown
    assert "Debt & Bonds" in res.allocation_breakdown
    assert res.tree_data.name == "Personalized Investment Strategy Tree"
    assert len(res.tree_data.children) >= 2


def test_market_overview_endpoint():
    """Tests GET /api/v1/investment-guide/market-overview."""
    response = client.get("/api/v1/investment-guide/market-overview")
    assert response.status_code == 200
    data = response.json()
    assert "nifty_50" in data
    assert "sensex" in data
    assert "market_direction" in data
    assert data["nifty_50"]["name"] == "NIFTY 50"


def test_opportunities_endpoint():
    """Tests GET /api/v1/investment-guide/opportunities."""
    response = client.get("/api/v1/investment-guide/opportunities?category=Stocks")
    assert response.status_code == 200
    cards = response.json()
    assert isinstance(cards, list)
    assert len(cards) > 0
    first = cards[0]
    assert "scores" in first
    assert "opportunity_score" in first["scores"]


def test_plan_generation_endpoint():
    """Tests POST /api/v1/investment-guide/plan."""
    payload = {
        "amount": 150000,
        "monthly_sip": 10000,
        "risk_profile": "aggressive",
        "horizon": "5+",
        "financial_goal": "Retirement Fund",
        "emergency_reserve_status": "adequate"
    }
    response = client.post("/api/v1/investment-guide/plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_profile"] == "Aggressive"
    assert "allocation_breakdown" in data
    assert "tree_data" in data


def test_market_status_endpoint():
    """Tests GET /api/v1/investment-guide/market-status."""
    response = client.get("/api/v1/investment-guide/market-status")
    assert response.status_code == 200
    data = response.json()
    assert "market_status" in data
    assert data["is_open"] is True
