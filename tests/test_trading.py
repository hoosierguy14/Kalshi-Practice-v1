"""Tests for the trading module."""

from unittest.mock import MagicMock

from src.trading import place_order, cancel_order, list_orders, _parse_order


class TestParseOrder:
    def test_parses_full_order(self):
        data = {
            "order_id": "order-123",
            "ticker": "KXBTC-TEST",
            "side": "yes",
            "action": "buy",
            "type": "limit",
            "yes_price": 45,
            "count": 2,
            "status": "resting",
            "created_time": "2025-02-17T12:00:00Z",
        }
        order = _parse_order(data)
        assert order.order_id == "order-123"
        assert order.price == 45
        assert order.count == 2

    def test_handles_no_side_price(self):
        data = {
            "order_id": "order-456",
            "ticker": "KXBTC-TEST",
            "side": "no",
            "action": "buy",
            "type": "limit",
            "no_price": 55,
            "count": 1,
            "status": "resting",
            "created_time": "2025-02-17T12:00:00Z",
        }
        order = _parse_order(data)
        assert order.price == 55


class TestPlaceOrder:
    def test_places_yes_buy_order(self):
        mock_client = MagicMock()
        mock_client.post.return_value = {
            "order": {
                "order_id": "new-order-1",
                "ticker": "KXBTC-TEST",
                "side": "yes",
                "action": "buy",
                "type": "limit",
                "yes_price": 40,
                "count": 1,
                "status": "resting",
                "created_time": "2025-02-17T12:00:00Z",
            }
        }

        order = place_order(
            mock_client, ticker="KXBTC-TEST", side="yes", count=1, yes_price=40,
        )
        assert order.order_id == "new-order-1"
        assert order.status == "resting"

        # Verify the right endpoint was called
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/portfolio/orders"


class TestCancelOrder:
    def test_cancels_order(self):
        mock_client = MagicMock()
        mock_client.delete.return_value = {}

        cancel_order(mock_client, "order-to-cancel")
        mock_client.delete.assert_called_once_with("/portfolio/orders/order-to-cancel")


class TestListOrders:
    def test_returns_order_list(self):
        mock_client = MagicMock()
        mock_client.get.return_value = {
            "orders": [
                {"order_id": "o1", "ticker": "T1", "side": "yes", "action": "buy",
                 "type": "limit", "yes_price": 40, "count": 1, "status": "resting",
                 "created_time": ""},
                {"order_id": "o2", "ticker": "T2", "side": "no", "action": "buy",
                 "type": "limit", "no_price": 60, "count": 2, "status": "executed",
                 "created_time": ""},
            ]
        }

        orders = list_orders(mock_client)
        assert len(orders) == 2
        assert orders[0].order_id == "o1"
        assert orders[1].status == "executed"
