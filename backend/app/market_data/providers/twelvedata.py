"""
Twelve Data API data provider adapter.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
import httpx

from app.market_data.base import StockDataProvider, IndexDataProvider
from app.market_data.schemas import StockQuote, StockSearchResult, IndexQuote
from app.market_data.exceptions import (
    ProviderTimeoutError,
    ProviderRateLimitedError,
    ProviderUnavailableError,
    InvalidSymbolError,
    DataNotFoundError,
    InvalidProviderResponseError,
)


class TwelveDataProvider(StockDataProvider, IndexDataProvider):
    """
    Adapter implementation using Twelve Data REST APIs.
    """

    def __init__(self, api_key: str, timeout_seconds: int = 15) -> None:
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._base_url = "https://api.twelvedata.com"

    async def _make_request(self, endpoint: str, params: dict) -> dict:
        params["apikey"] = self._api_key
        url = f"{self._base_url}/{endpoint.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=float(self._timeout)) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 429:
                    raise ProviderRateLimitedError("Twelve Data rate limit exceeded.")
                if resp.status_code != 200:
                    raise ProviderUnavailableError(f"Twelve Data returned HTTP status {resp.status_code}.")
                data = resp.json()
                if data.get("status") == "error":
                    code = data.get("code")
                    if code == 429:
                        raise ProviderRateLimitedError(data.get("message", "Rate limit"))
                    elif code == 404 or code == 400:
                        raise DataNotFoundError(data.get("message", "Not found"))
                    else:
                        raise ProviderUnavailableError(data.get("message", "API Error"))
                return data
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(f"Timeout calling Twelve Data API: {str(exc)}") from exc
        except httpx.RequestError as exc:
            raise ProviderUnavailableError(f"Error calling Twelve Data API: {str(exc)}") from exc

    async def get_quote(self, symbol: str, exchange: Optional[str] = None) -> StockQuote:
        data = await self._make_request("quote", {"symbol": symbol, "exchange": exchange or ""})
        
        price_str = data.get("close") or data.get("price")
        if not price_str:
            raise DataNotFoundError(f"No price quote found on Twelve Data for symbol: {symbol}")

        try:
            price = Decimal(str(price_str))
            prev_close = Decimal(str(data.get("previous_close", price_str)))
            change = Decimal(str(data.get("change", 0)))
            change_pct = Decimal(str(data.get("percent_change", 0)))
            currency = data.get("currency", "INR" if ".NS" in symbol or ".BO" in symbol else "USD")

            now = datetime.now(timezone.utc)
            return StockQuote(
                symbol=symbol,
                exchange=data.get("exchange") or exchange or "NSE",
                price=price,
                currency=currency,
                timestamp=now,
                data_as_of=now.isoformat(),
                freshness="REAL_TIME",
                provider="twelvedata",
                source="Twelve Data Quote API",
                previous_close=prev_close,
                change=change,
                change_percent=change_pct,
                market_status="OPEN" if data.get("is_market_open") else "CLOSED",
            )
        except Exception as exc:
            raise InvalidProviderResponseError(f"Failed to parse Twelve Data quote response: {str(exc)}") from exc

    async def search_stocks(self, query: str) -> List[StockSearchResult]:
        data = await self._make_request("symbol_search", {"symbol": query})
        
        raw_list = data.get("data", [])
        results: List[StockSearchResult] = []
        
        for item in raw_list:
            sym = item.get("symbol")
            name = item.get("instrument_name")
            exch = item.get("exchange", "")
            curr = item.get("currency", "USD")
            if sym and name:
                results.append(
                    StockSearchResult(
                        symbol=sym,
                        company_name=name,
                        exchange=exch,
                        currency=curr,
                        provider="twelvedata",
                    )
                )
        return results

    async def get_index_quote(self, index_name: str) -> IndexQuote:
        symbol_map = {
            "NIFTY_50": "NIFTY 50",
            "SENSEX": "BSESN",
            "BANK_NIFTY": "NIFTY BANK",
        }
        sym = symbol_map.get(index_name.upper(), index_name)
        data = await self._make_request("quote", {"symbol": sym})

        price_str = data.get("close") or data.get("price")
        if not price_str:
            raise DataNotFoundError(f"No index quote found on Twelve Data for: {index_name}")

        try:
            val = Decimal(str(price_str))
            change = Decimal(str(data.get("change", 0)))
            change_pct = Decimal(str(data.get("percent_change", 0)))

            now = datetime.now(timezone.utc)
            return IndexQuote(
                index_name=index_name,
                value=val,
                change=change,
                change_percent=change_pct,
                timestamp=now,
                data_as_of=now.isoformat(),
                freshness="REAL_TIME",
                provider="twelvedata",
            )
        except Exception as exc:
            raise InvalidProviderResponseError(f"Failed to parse Twelve Data index quote: {str(exc)}") from exc
