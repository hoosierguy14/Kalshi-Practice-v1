"""Tests for the markets module."""

from unittest.mock import MagicMock

from src.markets import Market, list_markets, get_market, _parse_market


class TestParseMarket:
    def test_parses_full_market_data(self):
        data = {
            "ticker": "KXBTC-25FEB17-T1800-B95500",
            "title": "Bitcoin above $95,500 at 6pm?",
            "status": "open",
            "yes_ask": 45,
            "yes_bid": 43,
            "no_ask": 57,
            "no_bid": 55,
            "volume": 1200,
            "open_interest": 300,
            "expiration_time": "2025-02-17T23:00:00Z",
            "result": "",
        }
        market = _parse_market(data)
        assert market.ticker == "KXBTC-25FEB17-T1800-B95500"
        assert market.yes_ask == 45
        assert market.status == "open"

    def test_handles_missing_fields(self):
        market = _parse_market({})
        assert market.ticker == ""
        assert market.yes_ask is None
        assert market.volume == 0


class TestListMarkets:
    def test_returns_markets_and_cursor(self):
        mock_client = MagicMock()
        mock_client.get.return_value = {
            "markets": [
                {"ticker": "MKT-1", "title": "Test 1", "status": "open",
                 "volume": 100, "open_interest": 50, "expiration_time": "", "result": ""},
                {"ticker": "MKT-2", "title": "Test 2", "status": "open",
                 "volume": 200, "open_interest": 75, "expiration_time": "", "result": ""},
            ],
            "cursor": "next-page-token",
        }

        markets, cursor = list_markets(mock_client, series_ticker="KXBTC")
        assert len(markets) == 2
        assert cursor == "next-page-token"
        assert markets[0].ticker == "MKT-1"

    def test_passes_params_correctly(self):
        mock_client = MagicMock()
        mock_client.get.return_value = {"markets": []}

        list_markets(mock_client, series_ticker="KXBTCMAXY", status="open", limit=50)
        mock_client.get.assert_called_once_with("/markets", params={
            "limit": 50,
            "series_ticker": "KXBTCMAXY",
            "status": "open",
        })


class TestGetMarket:
    def test_returns_single_market(self):
        mock_client = MagicMock()
        mock_client.get.return_value = {
            "market": {
                "ticker": "KXBTC-TEST",
                "title": "Test Market",
                "status": "open",
                "volume": 500,
                "open_interest": 100,
                "expiration_time": "2025-02-17T23:00:00Z",
                "result": "",
            }
        }

        market = get_market(mock_client, "KXBTC-TEST")
        assert market.ticker == "KXBTC-TEST"
        assert market.volume == 500
