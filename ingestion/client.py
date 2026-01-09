"""APEC API client."""

import requests
from typing import Any, Optional

from .config import BASE_URL, HEADERS, REQUEST_TIMEOUT


class ApecClient:
    """Simple client for APEC API using requests.Session."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.base_url = BASE_URL
        self.timeout = REQUEST_TIMEOUT

    def get(self, path: str, params: Optional[dict] = None) -> dict[str, Any]:
        """Make GET request to APEC API.

        Args:
            path: API endpoint path (e.g., "/rechercheOffre")
            params: Optional query parameters

        Returns:
            JSON response as dictionary

        Raises:
            requests.HTTPError: If request fails
        """
        url = f"{self.base_url}{path}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def post(self, path: str, data: Optional[dict] = None) -> dict[str, Any]:
        """Make POST request to APEC API.

        Args:
            path: API endpoint path (e.g., "/rechercheOffre")
            data: Optional JSON payload

        Returns:
            JSON response as dictionary

        Raises:
            requests.HTTPError: If request fails
        """
        url = f"{self.base_url}{path}"
        response = self.session.post(url, json=data, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
