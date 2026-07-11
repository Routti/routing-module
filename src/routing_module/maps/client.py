"""Shared HTTP client for OpenRouteService REST APIs."""

from typing import Any

import httpx

from routing_module.config import get_openrouteservice_api_key

ORS_BASE_URL = "https://api.openrouteservice.org"


class OrsClient:
    """Thin wrapper around httpx for OpenRouteService API calls."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or get_openrouteservice_api_key()
        self._client = httpx.Client(base_url=ORS_BASE_URL, timeout=30.0)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send a GET request to ORS."""
        response = self._client.get(path, params=params, headers=self._headers())
        response.raise_for_status()
        return response.json()

    def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        """Send a POST request to ORS."""
        response = self._client.post(path, json=body, headers=self._headers())
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "OrsClient":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
