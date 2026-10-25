"""Thin API client for automationexercise.com.

Quirk worth knowing (and a good interview talking point): this API always
answers with HTTP 200 and puts the *real* status in the JSON body as
`responseCode`. It also sends JSON with a `text/html` content type. The client
hides both quirks so tests assert on the business status, not the transport.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import requests

from config import settings


@dataclass
class ApiResponse:
    http_status: int
    body: dict[str, Any] = field(default_factory=dict)

    @property
    def code(self) -> int | None:
        """Business status reported by the API inside the JSON body."""
        return self.body.get("responseCode")

    @property
    def message(self) -> str | None:
        return self.body.get("message")


class AutomationExerciseAPI:
    def __init__(self, base_url: str = settings.API_BASE_URL, timeout: float = settings.API_TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    # ---------- low level ----------
    def _request(self, method: str, path: str, **kwargs) -> ApiResponse:
        response = self.session.request(method, f"{self.base_url}/{path.lstrip('/')}", timeout=self.timeout, **kwargs)
        try:
            body = json.loads(response.text)
        except json.JSONDecodeError:
            body = {"raw": response.text}
        return ApiResponse(http_status=response.status_code, body=body)

    # ---------- products & brands ----------
    def get_products(self) -> ApiResponse:
        return self._request("GET", "productsList")

    def post_products(self) -> ApiResponse:
        return self._request("POST", "productsList")

    def get_brands(self) -> ApiResponse:
        return self._request("GET", "brandsList")

    def put_brands(self) -> ApiResponse:
        return self._request("PUT", "brandsList")

    def search_products(self, term: str | None) -> ApiResponse:
        data = {} if term is None else {"search_product": term}
        return self._request("POST", "searchProduct", data=data)

    # ---------- accounts ----------
    def verify_login(self, email: str | None, password: str | None) -> ApiResponse:
        data = {k: v for k, v in {"email": email, "password": password}.items() if v is not None}
        return self._request("POST", "verifyLogin", data=data)

    def create_account(self, user: dict[str, str]) -> ApiResponse:
        return self._request("POST", "createAccount", data=user)

    def delete_account(self, email: str, password: str) -> ApiResponse:
        return self._request("DELETE", "deleteAccount", data={"email": email, "password": password})

    def get_user_by_email(self, email: str) -> ApiResponse:
        return self._request("GET", "getUserDetailByEmail", params={"email": email})
