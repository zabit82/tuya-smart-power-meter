"""Data update coordinator for Tuya Power Meter."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_API_HOST,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_DEVICE_IDS,
    CONF_POLL_INTERVAL,
    DEFAULT_HOST,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
)
from .tuya_api import TuyaAPIClient, TuyaAuthError, TuyaAPIError

_LOGGER = logging.getLogger(__name__)


class TuyaCoordinator(DataUpdateCoordinator):
    """Polls Tuya API for all configured devices."""

    def __init__(self, hass: HomeAssistant, entry_data: dict) -> None:
        self._client_id = entry_data[CONF_CLIENT_ID]
        self._client_secret = entry_data[CONF_CLIENT_SECRET]
        self._host = entry_data.get(CONF_API_HOST, DEFAULT_HOST)
        self._device_ids: list[str] = [
            d.strip()
            for d in entry_data.get(CONF_DEVICE_IDS, "").split(",")
            if d.strip()
        ]
        poll_interval = entry_data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=poll_interval),
        )

        self._session: aiohttp.ClientSession | None = None
        self._api: TuyaAPIClient | None = None

        # Cached device info (name, category, product) — fetched once
        self.devices: dict[str, dict] = {}

        # Cached property specs per device — fetched once
        self._specs: dict[str, dict[str, dict]] = {}

    def _get_api(self) -> TuyaAPIClient:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        if self._api is None:
            self._api = TuyaAPIClient(
                self._client_id, self._client_secret, self._host, self._session
            )
        return self._api

    async def async_shutdown(self) -> None:
        """Close the aiohttp session on integration unload."""
        if self._session and not self._session.closed:
            await self._session.close()
        await super().async_shutdown()

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch shadow properties for all devices.

        Returns:
            dict[device_id] = {
                "properties": list[dict],   # raw shadow properties
                "specs":      dict[code, dict],  # scale/unit/name per code
            }
        """
        api = self._get_api()

        try:
            # Ensure we have device metadata (only for the first run or new IDs)
            for device_id in self._device_ids:
                if device_id not in self.devices:
                    try:
                        self.devices[device_id] = await api.get_device(device_id)
                    except TuyaAuthError:
                        await api.authenticate()
                        self.devices[device_id] = await api.get_device(device_id)
                    _LOGGER.debug(
                        "Cached device info for %s: %s",
                        device_id,
                        self.devices[device_id].get("name"),
                    )

                if device_id not in self._specs:
                    self._specs[device_id] = await api.get_property_specs(device_id)

        except (TuyaAuthError, TuyaAPIError) as err:
            raise UpdateFailed(f"Device metadata fetch failed: {err}") from err

        # Now fetch live data for all devices
        result: dict[str, Any] = {}
        for device_id in self._device_ids:
            try:
                props = await api.get_shadow_properties(device_id)
                result[device_id] = {
                    "properties": props,
                    "specs": self._specs.get(device_id, {}),
                }
            except (TuyaAuthError, TuyaAPIError) as err:
                _LOGGER.warning("Failed to fetch data for %s: %s", device_id, err)
                # Keep previous data if available; still return partial result
                if self.data and device_id in self.data:
                    result[device_id] = self.data[device_id]

        return result
