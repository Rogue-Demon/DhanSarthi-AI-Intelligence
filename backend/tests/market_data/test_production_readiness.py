"""
Unit tests for production market data readiness, deterministic Silver/Gold conversion,
and truthful AI advisor metadata flags.
"""

from __future__ import annotations

from decimal import Decimal
from datetime import datetime, timezone
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.config import settings
from app.market_data.service import MarketDataService
from app.market_data.schemas import StockQuote, ExchangeRate
from app.market_data.exceptions import ProviderUnavailableError
from app.ai.advisor.service import AIAdvisorService
from app.ai.context.builder import AIContextBuilder


@pytest.mark.anyio
async def test_silver_deterministic_unit_conversion():
    """Verify XAGUSD (USD/troy oz) converts deterministically to INR/kg."""
    service = MarketDataService()
    
    # Mock stock quote for XAGUSD ($30.00 / troy oz)
    mock_quote = StockQuote(
        symbol="XAGUSD",
        exchange="COMMODITY",
        price=Decimal("30.00"),
        currency="USD",
        timestamp=datetime.now(timezone.utc),
        data_as_of="2026-08-23T10:00:00Z",
        freshness="REAL_TIME",
        provider="test_provider",
        source="Test Provider API",
        previous_close=Decimal("29.50"),
        change=Decimal("0.50"),
        change_percent=Decimal("1.69"),
    )
    
    # Mock FX rate (USD/INR = 85.00)
    mock_fx = ExchangeRate(
        base_currency="USD",
        quote_currency="INR",
        rate=Decimal("85.00"),
        timestamp=datetime.now(timezone.utc),
        data_as_of="2026-08-23T10:00:00Z",
        freshness="REAL_TIME",
        provider="test_fx",
        source="Test FX API",
    )
    
    with patch.object(service, "get_stock_quote", AsyncMock(return_value=mock_quote)):
        with patch.object(service, "get_exchange_rate", AsyncMock(return_value=mock_fx)):
            result = await service.get_commodity_quote("XAGUSD", target_currency="INR")
            
            assert result["available"] is True
            assert result["name"] == "Silver"
            assert result["original"]["price"] == 30.0
            assert result["original"]["currency"] == "USD"
            assert result["original"]["unit"] == "troy_oz"
            
            # Expected math:
            # 30.0 * (1000 / 31.1034768) * 85.0 = 81984.38
            expected_inr_kg = round((30.0 * (1000.0 / 31.1034768)) * 85.0, 2)
            assert result["display"]["price"] == expected_inr_kg
            assert result["display"]["currency"] == "INR"
            assert result["display"]["unit"] == "kg"
            
            assert result["conversion"] is not None
            assert result["conversion"]["fx_rate"] == 85.0
            assert "INR/kg" in result["conversion"]["formula"]


@pytest.mark.anyio
async def test_gold_deterministic_unit_conversion():
    """Verify XAUUSD (USD/troy oz) converts deterministically to INR/10g."""
    service = MarketDataService()
    
    mock_quote = StockQuote(
        symbol="XAUUSD",
        exchange="COMMODITY",
        price=Decimal("2500.00"),
        currency="USD",
        timestamp=datetime.now(timezone.utc),
        data_as_of="2026-08-23T10:00:00Z",
        freshness="REAL_TIME",
        provider="test_provider",
        source="Test Provider API",
        previous_close=Decimal("2490.00"),
        change=Decimal("10.00"),
        change_percent=Decimal("0.40"),
    )
    
    mock_fx = ExchangeRate(
        base_currency="USD",
        quote_currency="INR",
        rate=Decimal("85.00"),
        timestamp=datetime.now(timezone.utc),
        data_as_of="2026-08-23T10:00:00Z",
        freshness="REAL_TIME",
        provider="test_fx",
        source="Test FX API",
    )
    
    with patch.object(service, "get_stock_quote", AsyncMock(return_value=mock_quote)):
        with patch.object(service, "get_exchange_rate", AsyncMock(return_value=mock_fx)):
            result = await service.get_commodity_quote("XAUUSD", target_currency="INR")
            
            assert result["available"] is True
            assert result["name"] == "Gold"
            assert result["original"]["price"] == 2500.0
            
            # Expected math:
            # 2500.0 * (10 / 31.1034768) * 85.0 = 68320.34
            expected_inr_10g = round((2500.0 * (10.0 / 31.1034768)) * 85.0, 2)
            assert result["display"]["price"] == expected_inr_10g
            assert result["display"]["currency"] == "INR"
            assert result["display"]["unit"] == "10g"


@pytest.mark.anyio
async def test_missing_fx_rate_preserves_original_unit_without_fabrication():
    """Verify that when FX rate fails, original unit/price is returned without fabricated INR."""
    service = MarketDataService()
    
    mock_quote = StockQuote(
        symbol="XAGUSD",
        exchange="COMMODITY",
        price=Decimal("32.50"),
        currency="USD",
        timestamp=datetime.now(timezone.utc),
        data_as_of="2026-08-23T10:00:00Z",
        freshness="REAL_TIME",
        provider="test_provider",
        source="Test Provider API",
        previous_close=Decimal("32.00"),
        change=Decimal("0.50"),
        change_percent=Decimal("1.56"),
    )
    
    with patch.object(service, "get_stock_quote", AsyncMock(return_value=mock_quote)):
        with patch.object(service, "get_exchange_rate", AsyncMock(side_effect=ProviderUnavailableError("FX service down"))):
            result = await service.get_commodity_quote("XAGUSD", target_currency="INR")
            
            assert result["available"] is True
            assert result["original"]["price"] == 32.5
            assert result["original"]["unit"] == "troy_oz"
            assert result["display"]["currency"] == "USD"
            assert result["display"]["unit"] == "troy_oz"
            assert result["conversion"] is None
            assert result["conversion_error"] is not None


@pytest.mark.anyio
async def test_production_mode_does_not_fall_back_to_mock_prices():
    """Verify production mode raises exception on provider failure instead of returning mock data."""
    service = MarketDataService()
    
    with patch.object(service, "_is_production_mode", return_value=True):
        with patch.object(service.stock_provider, "get_quote", AsyncMock(side_effect=ProviderUnavailableError("API rate limit"))):
            with pytest.raises(ProviderUnavailableError):
                await service.get_stock_quote("RELIANCE.NS")


@pytest.mark.anyio
async def test_market_api_failure_returns_unavailable_state():
    """Verify get_commodity_quote returns available=False state on provider failure."""
    service = MarketDataService()
    
    with patch.object(service, "get_stock_quote", AsyncMock(side_effect=ProviderUnavailableError("API unreachable"))):
        result = await service.get_commodity_quote("XAGUSD")
        
        assert result["available"] is False
        assert "temporarily unavailable" in result["error"]
        assert result["source"] == "market_api"
