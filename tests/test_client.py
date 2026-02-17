"""Tests for the API client module."""

import tempfile
from unittest.mock import patch, MagicMock

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from src.client import KalshiClient, KalshiAPIError


@pytest.fixture
def mock_key_file():
    """Generate a temp RSA key file for testing."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    pem_data = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with tempfile.NamedTemporaryFile(suffix=".pem", delete=False) as f:
        f.write(pem_data)
        return f.name


@pytest.fixture
def client(mock_key_file):
    """Create a KalshiClient pointing to a fake URL with a test key."""
    return KalshiClient(
        api_key_id="test-key",
        private_key_path=mock_key_file,
        base_url="https://demo-api.kalshi.co/trade-api/v2",
    )


class TestKalshiClient:
    def test_initialization(self, client):
        assert client.api_key_id == "test-key"
        assert "demo-api" in client.base_url

    @patch("src.client.requests.Session.request")
    def test_get_success(self, mock_request, client):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"markets": []}
        mock_request.return_value = mock_response

        result = client.get("/markets")
        assert result == {"markets": []}

    @patch("src.client.requests.Session.request")
    def test_raises_on_api_error(self, mock_request, client):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.json.return_value = {"message": "Invalid API key"}
        mock_request.return_value = mock_response

        with pytest.raises(KalshiAPIError) as exc_info:
            client.get("/markets")
        assert exc_info.value.status_code == 401

    @patch("src.client.requests.Session.request")
    def test_handles_204_no_content(self, mock_request, client):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 204
        mock_request.return_value = mock_response

        result = client.delete("/portfolio/orders/some-id")
        assert result == {}
