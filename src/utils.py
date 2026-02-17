"""
Shared utility functions.

Small helper functions used across the project.
"""

import logging
import sys
from datetime import datetime, timezone

from config import settings


def setup_logging() -> None:
    """
    Configure logging for the entire application.

    Sets up a consistent log format so you can see timestamps
    and which module each message came from.
    """
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def cents_to_dollars(cents: int) -> float:
    """Convert cents to dollars. Kalshi prices are in cents."""
    return cents / 100


def dollars_to_cents(dollars: float) -> int:
    """Convert dollars to cents for the Kalshi API."""
    return int(dollars * 100)


def now_utc() -> datetime:
    """Get the current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


def format_price(cents: int | None) -> str:
    """
    Format a price in cents as a human-readable string.

    Examples:
        format_price(45)  -> "$0.45"
        format_price(None) -> "N/A"
    """
    if cents is None:
        return "N/A"
    return f"${cents / 100:.2f}"


def format_pnl(cents: int) -> str:
    """
    Format a profit/loss value with a + or - sign.

    Examples:
        format_pnl(150)  -> "+$1.50"
        format_pnl(-50)  -> "-$0.50"
        format_pnl(0)    -> "$0.00"
    """
    if cents > 0:
        return f"+${cents / 100:.2f}"
    elif cents < 0:
        return f"-${abs(cents) / 100:.2f}"
    return "$0.00"
