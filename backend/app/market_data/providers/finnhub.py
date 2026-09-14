"""
Finnhub API data provider adapter.
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


class FinnhubProvider(StockDataProvider):
    """
    Adapter implementation using Finnhub REST APIs.
    """

    def __init__(self, api_key: str, timeout_seconds: int = 15) -> None:
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._base_url = "https://finnhub.io/api/v1"

    async def _make_request(self, endpoint: str, params: dict) -> dict:
        params["token"] = self._api_key
        url = f"{self._base_url}/{endpoint.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=float(self._timeout)) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 429:
                    raise ProviderRateLimitedError("Finnhub rate limit exceeded.")
                if resp.status_code != 200:
                    raise ProviderUnavailableError(f"Finnhub returned HTTP status {resp.status_code}.")
                return resp.json()
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(f"Timeout calling Finnhub API: {str(exc)}") from exc
        except httpx.RequestError as exc:
            raise ProviderUnavailableError(f"Error calling Finnhub API: {str(exc)}") from exc

    async def get_quote(self, symbol: str, exchange: Optional[str] = None) -> StockQuote:
        data = await self._make_request("quote", {"symbol": symbol})
        
        c = data.get("c")  # Current price
        if c is None or c == 0:
            raise DataNotFoundError(f"No valid quote found on Finnhub for symbol: {symbol}")

        try:
            price = Decimal(str(c))
            prev_close = Decimal(str(data.get("pc", 0)))
            change = Decimal(str(data.get("d", 0)))
            change_pct = Decimal(str(data.get("dp", 0)))

            now = datetime.now(timezone.utc)
            return StockQuote(
                symbol=symbol,
                exchange=exchange or "US",
                price=price,
                currency="USD",
                timestamp=now,
                data_as_of=now.isoformat(),
                freshness="REAL_TIME",
                provider="finnhub",
                source="Finnhub Quote API",
                previous_close=prev_close,
                change=change,
                change_percent=change_pct,
                market_status="OPEN",
            )
        except Exception as exc:
            raise InvalidProviderResponseError(f"Failed to parse Finnhub quote response: {str(exc)}") from exc

    async def search_stocks(self, query: str) -> List[StockSearchResult]:
        data = await self._make_request("search", {"q": query})
        
        results_raw = data.get("result", [])
        results: List[StockSearchResult] = []
        
        for item in results_raw:
            sym = item.get("symbol")
            desc = item.get("description")
            display_sym = item.get("displaySymbol", sym)
            if sym and desc:
                results.append(
                    StockSearchResult(
                        symbol=sym,
                        company_name=desc,
                        exchange=display_sym,
                        currency="USD",
                        provider="finnhub",
                    )
                )
        return results
