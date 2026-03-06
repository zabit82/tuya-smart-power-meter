"""Async Tuya OpenAPI client for Home Assistant."""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

EMPTY_BODY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def _now_ms() -> str:
    return str(int(time.time() * 1000))


def _hmac_sha256(secret: str, payload: str) -> str:
    return hmac.new(
        secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest().upper()


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _string_to_sign(method: str, body: str, url_path: str) -> str:
    """Build the canonical string to sign per Tuya v2 signature spec."""
    body_hash = EMPTY_BODY_SHA256 if not body else _sha256(body)
    return "\n".join([method.upper(), body_hash, "", url_path])


class TuyaAuthError(Exception):
    """Raised when authentication fails."""


class TuyaAPIError(Exception):
    """Raised when a Tuya API call fails."""


class TuyaAPIClient:
    """Async client for the Tuya OpenAPI."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        host: str,
        session: aiohttp.ClientSession,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._host = host.rstrip("/")
        self._session = session
        self._access_token: str = ""

    async def authenticate(self) -> None:
        """Fetch a new access token (grant_type=1)."""
        t = _now_ms()
        url_path = "/v1.0/token?grant_type=1"
        sts = _string_to_sign("GET", "", url_path)
        sig = _hmac_sha256(self._client_secret, self._client_id + t + sts)

        headers = {
            "client_id": self._client_id,
            "t": t,
            "sign": sig,
            "sign_method": "HMAC-SHA256",
            "Content-Type": "application/json",
        }
        async with self._session.get(
            self._host + url_path, headers=headers
        ) as resp:
            data = await resp.json(content_type=None)

        if not data.get("success"):
            raise TuyaAuthError(f"Auth failed: {data.get('msg')} — {data}")

        self._access_token = data["result"]["access_token"]
        _LOGGER.debug("Tuya token obtained successfully")

    async def _get(self, url_path: str) -> Any:
        """Authenticated GET request with auto-reauth on token expiry."""
        if not self._access_token:
            await self.authenticate()

        result = await self._get_raw(url_path)

        # Token expired — reauthenticate once and retry
        if not result.get("success") and result.get("code") in (1010, 1011, 1012):
            _LOGGER.debug("Token expired, refreshing...")
            await self.authenticate()
            result = await self._get_raw(url_path)

        return result

    async def _get_raw(self, url_path: str) -> Any:
        t = _now_ms()
        sts = _string_to_sign("GET", "", url_path)
        sig = _hmac_sha256(
            self._client_secret, self._client_id + self._access_token + t + sts
        )
        headers = {
            "client_id": self._client_id,
            "access_token": self._access_token,
            "t": t,
            "sign": sig,
            "sign_method": "HMAC-SHA256",
            "Content-Type": "application/json",
        }
        async with self._session.get(
            self._host + url_path, headers=headers
        ) as resp:
            return await resp.json(content_type=None)

    async def get_device(self, device_id: str) -> dict:
        """Get device info from /v1.0/devices/{id}."""
        data = await self._get(f"/v1.0/devices/{device_id}")
        if not data.get("success"):
            raise TuyaAPIError(f"get_device({device_id}) failed: {data.get('msg')}")
        return data["result"]

    async def get_shadow_properties(self, device_id: str) -> list[dict]:
        """Get live DPS from /v2.0/cloud/thing/{id}/shadow/properties."""
        data = await self._get(
            f"/v2.0/cloud/thing/{device_id}/shadow/properties"
        )
        if not data.get("success"):
            raise TuyaAPIError(
                f"get_shadow_properties({device_id}) failed: {data.get('msg')}"
            )
        return data["result"]["properties"]

    async def get_property_specs(self, device_id: str) -> dict[str, dict]:
        """Get model spec from /v2.0/cloud/thing/{id}/model.

        Returns a dict: code → {name, scale, unit, type}
        """
        data = await self._get(f"/v2.0/cloud/thing/{device_id}/model")
        if not data.get("success"):
            return {}

        try:
            model = json.loads(data["result"]["model"])
        except (KeyError, json.JSONDecodeError):
            return {}

        specs: dict[str, dict] = {}
        for service in model.get("services", []):
            for prop in service.get("properties", []):
                code = prop.get("code", "")
                ts = prop.get("typeSpec", {})
                specs[code] = {
                    "name": prop.get("name", code),
                    "scale": float(ts.get("scale", 0)),
                    "unit": ts.get("unit", ""),
                    "type": ts.get("type", ""),
                }
        return specs
