"""
Marketstack API data provider adapter.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
import httpx

from app.market_data.base import StockDataProvider
from app.market_data.schemas import StockQuote, StockSearchResult
from app.market_data.exceptions import (
    ProviderTimeoutError,
    ProviderRateLimitedError,
    ProviderUnavailableError,
    InvalidSymbolError,
    DataNotFoundError,
    InvalidProviderResponseError,
)


class MarketstackProvider(StockDataProvider):
    """
    Adapter implementation using Marketstack REST APIs.
    """

    def __init__(self, api_key: str, timeout_seconds: int = 15) -> None:
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._base_url = "http://api.marketstack.com/v1"

    async def _make_request(self, endpoint: str, params: dict) -> dict:
        params["access_key"] = self._api_key
        url = f"{self._base_url}/{endpoint.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=float(self._timeout)) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 429:
                    raise ProviderRateLimitedError("Marketstack rate limit exceeded.")
                if resp.status_code != 200:
                    raise ProviderUnavailableError(f"Marketstack returned HTTP status {resp.status_code}.")
                data = resp.json()
                if "error" in data:
                    err = data["error"]
                    raise ProviderUnavailableError(f"Marketstack error: {err.get('message')}")
                return data
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(f"Timeout calling Marketstack API: {str(exc)}") from exc
        except httpx.RequestError as exc:
            raise ProviderUnavailableError(f"Error calling Marketstack API: {str(exc)}") from exc

    async def get_quote(self, symbol: str, exchange: Optional[str] = None) -> StockQuote:
        data = await self._make_request("eod/latest", {"symbols": symbol})
        
        data_list = data.get("data", [])
        if not data_list:
            raise DataNotFoundError(f"No EOD quote found on Marketstack for symbol: {symbol}")

        item = data_list[0]
        close_price = item.get("close")
        if close_price is None:
            raise DataNotFoundError(f"Missing close price for symbol: {symbol}")

        try:
            price = Decimal(str(close_price))
            open_price = Decimal(str(item.get("open", close_price)))
            change = price - open_price
            change_pct = (change / open_price * Decimal("100")) if open_price > 0 else Decimal("0")

            now = datetime.now(timezone.utc)
            return StockQuote(
                symbol=symbol,
                exchange=item.get("exchange") or exchange or "NSE",
                price=price,
                currency="INR" if ".NS" in symbol else "USD",
                timestamp=now,
                data_as_of=item.get("date", now.isoformat()),
                freshness="DELAYED",
                provider="marketstack",
                source="Marketstack EOD API",
                previous_close=open_price,
                change=change,
                change_percent=change_pct,
                market_status="CLOSED",
            )
        except Exception as exc:
            raise InvalidProviderResponseError(f"Failed to parse Marketstack response: {str(exc)}") from exc

    async def search_stocks(self, query: str) -> List[StockSearchResult]:
        data = await self._make_request("tickers", {"search": query})
        
        tickers = data.get("data", [])
        results: List[StockSearchResult] = []
        
        for item in tickers:
            sym = item.get("symbol")
            name = item.get("name")
            exch = item.get("stock_exchange", {}).get("acronym", "US")
            if sym and name:
                results.append(
                    StockSearchResult(
                        symbol=sym,
                        company_name=name,
                        exchange=exch,
                        currency="USD",
                        provider="marketstack",
                    )
                )
        return results
