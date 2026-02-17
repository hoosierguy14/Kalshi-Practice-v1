"""Tests for the authentication module."""

import base64
import tempfile
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from src.auth import build_auth_headers, load_private_key, sign_request


@pytest.fixture
def test_key_pair():
    """Generate a temporary RSA key pair for testing."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    return private_key


@pytest.fixture
def test_key_file(test_key_pair):
    """Write the test private key to a temp file and return the path."""
    pem_data = test_key_pair.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with tempfile.NamedTemporaryFile(suffix=".pem", delete=False) as f:
        f.write(pem_data)
        return f.name


class TestLoadPrivateKey:
    def test_loads_valid_key(self, test_key_file):
        key = load_private_key(test_key_file)
        assert key is not None

    def test_raises_on_missing_file(self):
        with pytest.raises(FileNotFoundError, match="Private key not found"):
            load_private_key("/nonexistent/path/key.pem")


class TestSignRequest:
    def test_returns_base64_string(self, test_key_pair):
        signature = sign_request(test_key_pair, "1234567890GET/trade-api/v2/markets")
        # Should be valid base64
        decoded = base64.b64decode(signature)
        assert len(decoded) > 0

    def test_different_messages_give_different_signatures(self, test_key_pair):
        sig1 = sign_request(test_key_pair, "message_one")
        sig2 = sign_request(test_key_pair, "message_two")
        assert sig1 != sig2


class TestBuildAuthHeaders:
    def test_returns_required_headers(self, test_key_pair):
        headers = build_auth_headers(
            api_key_id="test-key-123",
            private_key=test_key_pair,
            method="GET",
            path="/trade-api/v2/markets",
        )
        assert "KALSHI-ACCESS-KEY" in headers
        assert "KALSHI-ACCESS-TIMESTAMP" in headers
        assert "KALSHI-ACCESS-SIGNATURE" in headers

    def test_key_id_matches(self, test_key_pair):
        headers = build_auth_headers(
            api_key_id="my-key-id",
            private_key=test_key_pair,
            method="GET",
            path="/trade-api/v2/markets",
        )
        assert headers["KALSHI-ACCESS-KEY"] == "my-key-id"

    def test_timestamp_is_numeric_string(self, test_key_pair):
        headers = build_auth_headers(
            api_key_id="test",
            private_key=test_key_pair,
            method="GET",
            path="/trade-api/v2/markets",
        )
        assert headers["KALSHI-ACCESS-TIMESTAMP"].isdigit()
