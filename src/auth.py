"""
Authentication for the Kalshi API.

Kalshi doesn't use simple API tokens. Instead, every request must be
cryptographically signed with your RSA private key. This module handles:

1. Loading your private key from a .pem file
2. Signing each request with RSA-PSS (SHA-256)
3. Building the auth headers that Kalshi expects
"""

import base64
import time
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def load_private_key(key_path: str) -> rsa.RSAPrivateKey:
    """
    Read an RSA private key from a .pem file on disk.

    Args:
        key_path: Path to your .pem file (e.g., "./keys/kalshi_private_key.pem")

    Returns:
        An RSA private key object ready for signing.

    Raises:
        FileNotFoundError: If the key file doesn't exist.
        ValueError: If the file isn't a valid RSA private key.
    """
    path = Path(key_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Private key not found at '{key_path}'. "
            f"Check your KALSHI_PRIVATE_KEY_PATH in .env"
        )

    key_data = path.read_bytes()
    private_key = serialization.load_pem_private_key(key_data, password=None)

    if not isinstance(private_key, rsa.RSAPrivateKey):
        raise ValueError(f"Expected RSA private key, got {type(private_key).__name__}")

    return private_key


def sign_request(private_key: rsa.RSAPrivateKey, message: str) -> str:
    """
    Sign a message string using RSA-PSS with SHA-256.

    This is the core of Kalshi's auth system. The message is typically:
        timestamp_ms + "GET" + "/trade-api/v2/markets"

    Args:
        private_key: Your loaded RSA private key.
        message: The string to sign (timestamp + method + path).

    Returns:
        Base64-encoded signature string.
    """
    signature_bytes = private_key.sign(
        message.encode("utf-8"),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH,
        ),
        hashes.SHA256(),
    )
    return base64.b64encode(signature_bytes).decode("utf-8")


def build_auth_headers(
    api_key_id: str,
    private_key: rsa.RSAPrivateKey,
    method: str,
    path: str,
) -> dict[str, str]:
    """
    Build the three authentication headers Kalshi requires on every request.

    Args:
        api_key_id: Your Kalshi API key ID.
        private_key: Your loaded RSA private key.
        method: HTTP method in uppercase (e.g., "GET", "POST", "DELETE").
        path: The API path WITHOUT query parameters.
              Example: "/trade-api/v2/markets" (not "/trade-api/v2/markets?limit=10")

    Returns:
        Dictionary with the three required headers.
    """
    # Timestamp in milliseconds as a string
    timestamp_ms = str(int(time.time() * 1000))

    # The message to sign: timestamp + METHOD + path
    message = timestamp_ms + method.upper() + path

    # Sign it
    signature = sign_request(private_key, message)

    return {
        "KALSHI-ACCESS-KEY": api_key_id,
        "KALSHI-ACCESS-TIMESTAMP": timestamp_ms,
        "KALSHI-ACCESS-SIGNATURE": signature,
    }
