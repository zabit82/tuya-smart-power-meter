"""Config flow for Tuya Power Meter integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

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
from .tuya_api import TuyaAPIClient, TuyaAuthError

_LOGGER = logging.getLogger(__name__)

STEP_CREDENTIALS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CLIENT_ID): str,
        vol.Required(CONF_CLIENT_SECRET): str,
        vol.Optional(CONF_API_HOST, default=DEFAULT_HOST): str,
    }
)

STEP_DEVICES_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_IDS): str,
        vol.Optional(CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=10, max=3600)
        ),
    }
)


class TuyaPowerMeterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Tuya Power Meter."""

    VERSION = 1

    def __init__(self) -> None:
        self._credentials: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 1: Enter Client ID and Secret."""
        errors: dict[str, str] = {}

        if user_input is not None:
            client_id = user_input[CONF_CLIENT_ID].strip()
            client_secret = user_input[CONF_CLIENT_SECRET].strip()
            host = user_input.get(CONF_API_HOST, DEFAULT_HOST).rstrip("/")

            # Validate credentials by obtaining a token
            try:
                async with aiohttp.ClientSession() as session:
                    api = TuyaAPIClient(client_id, client_secret, host, session)
                    await api.authenticate()
            except TuyaAuthError:
                errors["base"] = "invalid_auth"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during Tuya auth")
                errors["base"] = "unknown"
            else:
                # Store credentials, move to device configuration step
                self._credentials = {
                    CONF_CLIENT_ID: client_id,
                    CONF_CLIENT_SECRET: client_secret,
                    CONF_API_HOST: host,
                }
                return await self.async_step_devices()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_CREDENTIALS_SCHEMA,
            errors=errors,
        )

    async def async_step_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2: Enter Device IDs and poll interval."""
        errors: dict[str, str] = {}

        if user_input is not None:
            device_ids_raw = user_input[CONF_DEVICE_IDS].strip()
            poll_interval = user_input.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)

            if not device_ids_raw:
                errors[CONF_DEVICE_IDS] = "device_ids_required"
            else:
                data = {
                    **self._credentials,
                    CONF_DEVICE_IDS: device_ids_raw,
                    CONF_POLL_INTERVAL: poll_interval,
                }
                return self.async_create_entry(
                    title=f"Tuya ({self._credentials[CONF_CLIENT_ID][:8]}…)",
                    data=data,
                )

        return self.async_show_form(
            step_id="devices",
            data_schema=STEP_DEVICES_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "TuyaOptionsFlow":
        return TuyaOptionsFlow(config_entry)


class TuyaOptionsFlow(config_entries.OptionsFlow):
    """Allow changing Device IDs and poll interval after setup."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self._config_entry.data
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_DEVICE_IDS,
                    default=current.get(CONF_DEVICE_IDS, ""),
                ): str,
                vol.Optional(
                    CONF_POLL_INTERVAL,
                    default=current.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
