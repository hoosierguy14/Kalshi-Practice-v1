"""
Market discovery and data retrieval.

This module helps you find and inspect Kalshi markets, especially
Bitcoin (BTC) prediction contracts. Key operations:

- List available markets (with filters)
- Get details for a specific market
- Get the order book (current bids/asks) for a market
"""

import logging
from dataclasses import dataclass

from src.client import KalshiClient

logger = logging.getLogger(__name__)


@dataclass
class Market:
    """Simplified representation of a Kalshi market."""

    ticker: str                # e.g., "KXBTC-25FEB17-T1800-B95500"
    title: str                 # e.g., "Bitcoin above $95,500 at 6pm?"
    status: str                # "open", "closed", "settled"
    yes_ask: int | None        # Lowest ask price for Yes (in cents)
    yes_bid: int | None        # Highest bid price for Yes (in cents)
    no_ask: int | None         # Lowest ask price for No (in cents)
    no_bid: int | None         # Highest bid price for No (in cents)
    volume: int                # Number of contracts traded
    open_interest: int         # Contracts currently outstanding
    expiration_time: str       # ISO 8601 timestamp
    result: str                # "yes", "no", or "" if not settled


def list_markets(
    client: KalshiClient,
    series_ticker: str | None = None,
    status: str | None = None,
    limit: int = 100,
    cursor: str | None = None,
) -> tuple[list[Market], str | None]:
    """
    Fetch a list of markets from Kalshi.

    Args:
        client: An authenticated KalshiClient.
        series_ticker: Filter by series (e.g., "KXBTCMAXY" for BTC yearly high).
        status: Filter by status ("open", "closed", "settled").
        limit: Max number of markets to return (1-200).
        cursor: Pagination cursor from a previous response.

    Returns:
        Tuple of (list of Market objects, next cursor string or None).
    """
    params: dict = {"limit": limit}
    if series_ticker:
        params["series_ticker"] = series_ticker
    if status:
        params["status"] = status
    if cursor:
        params["cursor"] = cursor

    data = client.get("/markets", params=params)

    markets = [_parse_market(m) for m in data.get("markets", [])]
    next_cursor = data.get("cursor")

    logger.info("Fetched %d markets (series=%s, status=%s)", len(markets), series_ticker, status)
    return markets, next_cursor


def get_market(client: KalshiClient, ticker: str) -> Market:
    """
    Get details for a single market by its ticker.

    Args:
        client: An authenticated KalshiClient.
        ticker: The market ticker (e.g., "KXBTC-25FEB17-T1800-B95500").

    Returns:
        A Market object with current data.
    """
    data = client.get(f"/markets/{ticker}")
    market_data = data.get("market", data)
    return _parse_market(market_data)


@dataclass
class OrderBookLevel:
    """A single price level in the order book."""

    price: int   # Price in cents (1-99)
    quantity: int  # Number of contracts


@dataclass
class OrderBook:
    """The order book for a market — all current bids and asks."""

    ticker: str
    yes_bids: list[OrderBookLevel]  # People wanting to buy Yes
    yes_asks: list[OrderBookLevel]  # People wanting to sell Yes
    no_bids: list[OrderBookLevel]   # People wanting to buy No
    no_asks: list[OrderBookLevel]   # People wanting to sell No


def get_orderbook(client: KalshiClient, ticker: str) -> OrderBook:
    """
    Get the current order book for a market.

    The order book shows all resting orders — what prices people
    are willing to buy/sell at and how many contracts.

    Args:
        client: An authenticated KalshiClient.
        ticker: The market ticker.

    Returns:
        An OrderBook with bids and asks for both sides.
    """
    data = client.get(f"/markets/{ticker}/orderbook")
    orderbook = data.get("orderbook", data)

    return OrderBook(
        ticker=ticker,
        yes_bids=_parse_levels(orderbook.get("yes", []), side="bids"),
        yes_asks=_parse_levels(orderbook.get("yes", []), side="asks"),
        no_bids=_parse_levels(orderbook.get("no", []), side="bids"),
        no_asks=_parse_levels(orderbook.get("no", []), side="asks"),
    )


def find_btc_markets(client: KalshiClient, status: str = "open") -> list[Market]:
    """
    Find all open Bitcoin-related markets.

    This is a convenience function that searches common BTC series tickers.

    Args:
        client: An authenticated KalshiClient.
        status: Market status filter (default "open").

    Returns:
        List of BTC Market objects.
    """
    btc_series = ["KXBTCMAXY", "KXBTCMINY", "KXBTC"]
    all_markets: list[Market] = []

    for series in btc_series:
        try:
            markets, _ = list_markets(client, series_ticker=series, status=status)
            all_markets.extend(markets)
        except Exception as e:
            logger.warning("Failed to fetch markets for series %s: %s", series, e)

    logger.info("Found %d BTC markets total", len(all_markets))
    return all_markets


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_market(data: dict) -> Market:
    """Convert raw API response dict into a Market dataclass."""
    return Market(
        ticker=data.get("ticker", ""),
        title=data.get("title", data.get("subtitle", "")),
        status=data.get("status", ""),
        yes_ask=data.get("yes_ask"),
        yes_bid=data.get("yes_bid"),
        no_ask=data.get("no_ask"),
        no_bid=data.get("no_bid"),
        volume=data.get("volume", 0),
        open_interest=data.get("open_interest", 0),
        expiration_time=data.get("expiration_time", ""),
        result=data.get("result", ""),
    )


def _parse_levels(levels_data: list, side: str) -> list[OrderBookLevel]:
    """Parse order book price levels from the API response."""
    result = []
    for level in levels_data:
        if isinstance(level, dict):
            result.append(OrderBookLevel(
                price=level.get("price", 0),
                quantity=level.get("quantity", 0),
            ))
    return result
