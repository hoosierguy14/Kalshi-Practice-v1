"""
Kalshi API client.

This is the central piece that all other modules use. It handles:
- Sending HTTP requests to the Kalshi API
- Automatically signing every request with your RSA key
- Rate limiting and retry logic for 429 errors
- Parsing JSON responses and surfacing errors clearly
"""

import logging
import time
from urllib.parse import urlparse

import requests

from config import settings
from src.auth import build_auth_headers, load_private_key

logger = logging.getLogger(__name__)


class KalshiAPIError(Exception):
    """Raised when the Kalshi API returns an error response."""

    def __init__(self, status_code: int, message: str, response: dict | None = None):
        self.status_code = status_code
        self.response = response or {}
        super().__init__(f"Kalshi API error {status_code}: {message}")


class KalshiClient:
    """
    HTTP client for the Kalshi trading API.

    Usage:
        client = KalshiClient()
        markets = client.get("/markets", params={"limit": 10})
        client.post("/portfolio/orders", json={"ticker": "...", ...})
    """

    def __init__(
        self,
        api_key_id: str | None = None,
        private_key_path: str | None = None,
        base_url: str | None = None,
    ):
        """
        Initialize the client.

        Args:
            api_key_id: Your API key (defaults to settings.API_KEY_ID).
            private_key_path: Path to .pem key (defaults to settings.PRIVATE_KEY_PATH).
            base_url: API base URL (defaults to settings.BASE_URL).
        """
        self.api_key_id = api_key_id or settings.API_KEY_ID
        self.base_url = base_url or settings.BASE_URL
        self.session = requests.Session()

        # Load the private key once so we don't re-read the file every request
        key_path = private_key_path or settings.PRIVATE_KEY_PATH
        self.private_key = load_private_key(key_path)

        logger.info("KalshiClient initialized (env=%s, base_url=%s)", settings.ENV, self.base_url)

    def request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        json: dict | None = None,
    ) -> dict:
        """
        Send an authenticated request to the Kalshi API.

        Args:
            method: HTTP method ("GET", "POST", "DELETE").
            endpoint: API endpoint (e.g., "/markets" or "/portfolio/orders").
            params: Query parameters (for GET requests).
            json: JSON body (for POST/PUT requests).

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            KalshiAPIError: If the API returns a non-2xx status.
        """
        url = self.base_url + endpoint

        # Kalshi wants us to sign with the full path (e.g., /trade-api/v2/markets)
        # but WITHOUT query parameters
        parsed = urlparse(url)
        sign_path = parsed.path

        # Build auth headers
        auth_headers = build_auth_headers(
            api_key_id=self.api_key_id,
            private_key=self.private_key,
            method=method.upper(),
            path=sign_path,
        )

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **auth_headers,
        }

        # Retry loop for rate limiting (429 errors)
        for attempt in range(settings.RATE_LIMIT_MAX_RETRIES):
            try:
                response = self.session.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=params,
                    json=json,
                    timeout=30,
                )

                # Rate limited — back off and retry
                if response.status_code == 429:
                    wait_time = settings.RATE_LIMIT_BACKOFF_BASE ** attempt
                    logger.warning(
                        "Rate limited (429). Waiting %.1fs before retry %d/%d",
                        wait_time,
                        attempt + 1,
                        settings.RATE_LIMIT_MAX_RETRIES,
                    )
                    time.sleep(wait_time)
                    continue

                # Any other error
                if not response.ok:
                    error_body = {}
                    try:
                        error_body = response.json()
                    except ValueError:
                        pass
                    error_msg = error_body.get("message", response.text[:200])
                    raise KalshiAPIError(response.status_code, error_msg, error_body)

                # Success — return parsed JSON (or empty dict for 204 No Content)
                if response.status_code == 204:
                    return {}
                return response.json()

            except requests.exceptions.RequestException as e:
                if attempt < settings.RATE_LIMIT_MAX_RETRIES - 1:
                    wait_time = settings.RATE_LIMIT_BACKOFF_BASE ** attempt
                    logger.warning("Request failed: %s. Retrying in %.1fs", e, wait_time)
                    time.sleep(wait_time)
                else:
                    raise

        raise KalshiAPIError(429, "Max retries exceeded due to rate limiting")

    # -----------------------------------------------------------------------
    # Convenience methods (so you can write client.get(...) instead of
    # client.request("GET", ...))
    # -----------------------------------------------------------------------

    def get(self, endpoint: str, params: dict | None = None) -> dict:
        """Send a GET request."""
        return self.request("GET", endpoint, params=params)

    def post(self, endpoint: str, json: dict | None = None) -> dict:
        """Send a POST request."""
        return self.request("POST", endpoint, json=json)

    def delete(self, endpoint: str) -> dict:
        """Send a DELETE request."""
        return self.request("DELETE", endpoint)
