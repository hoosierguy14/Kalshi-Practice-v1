"""Tests for the strategy module."""

from unittest.mock import MagicMock

from src.markets import Market
from src.portfolio import Balance, Position
from src.strategy import SimpleStrategy


def _make_market(
    ticker: str = "KXBTC-TEST",
    yes_ask: int | None = 35,
    no_ask: int | None = 65,
    status: str = "open",
) -> Market:
    """Helper to create a Market for testing."""
    return Market(
        ticker=ticker,
        title="Test Market",
        status=status,
        yes_ask=yes_ask,
        yes_bid=yes_ask - 2 if yes_ask else None,
        no_ask=no_ask,
        no_bid=no_ask - 2 if no_ask else None,
        volume=100,
        open_interest=50,
        expiration_time="2025-02-17T23:00:00Z",
        result="",
    )


class TestSimpleStrategy:
    def setup_method(self):
        self.strategy = SimpleStrategy(
            max_price_cents=40,
            min_price_cents=5,
            contracts_per_trade=1,
        )
        self.mock_client = MagicMock()

    def test_generates_signal_for_cheap_yes(self):
        markets = [_make_market(yes_ask=30)]
        balance = Balance(available_balance=10000, total_balance=10000)

        signals = self.strategy.evaluate(self.mock_client, markets, balance, positions=[])
        assert len(signals) == 1
        assert signals[0].side == "yes"
        assert signals[0].price == 30

    def test_skips_expensive_markets(self):
        markets = [_make_market(yes_ask=60, no_ask=80)]
        balance = Balance(available_balance=10000, total_balance=10000)

        signals = self.strategy.evaluate(self.mock_client, markets, balance, positions=[])
        assert len(signals) == 0

    def test_skips_when_balance_too_low(self):
        markets = [_make_market(yes_ask=30)]
        balance = Balance(available_balance=500, total_balance=500)  # Below MIN_BALANCE_CENTS

        signals = self.strategy.evaluate(self.mock_client, markets, balance, positions=[])
        assert len(signals) == 0

    def test_skips_already_held_tickers(self):
        markets = [_make_market(ticker="KXBTC-HELD", yes_ask=30)]
        balance = Balance(available_balance=10000, total_balance=10000)
        positions = [
            Position(
                ticker="KXBTC-HELD", market_title="Held", side="yes",
                count=1, avg_price=30, market_value=35, realized_pnl=0,
            )
        ]

        signals = self.strategy.evaluate(self.mock_client, markets, balance, positions=positions)
        assert len(signals) == 0

    def test_skips_closed_markets(self):
        markets = [_make_market(status="closed", yes_ask=30)]
        balance = Balance(available_balance=10000, total_balance=10000)

        signals = self.strategy.evaluate(self.mock_client, markets, balance, positions=[])
        assert len(signals) == 0

    def test_picks_no_side_when_yes_too_expensive(self):
        markets = [_make_market(yes_ask=60, no_ask=35)]
        balance = Balance(available_balance=10000, total_balance=10000)

        signals = self.strategy.evaluate(self.mock_client, markets, balance, positions=[])
        assert len(signals) == 1
        assert signals[0].side == "no"
