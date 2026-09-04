"""Binary sensor platform for Tuya Power Meter."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BINARY_SENSOR_MAP, CODE_NAMES, DOMAIN
from .coordinator import TuyaCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tuya Power Meter binary sensors from a config entry."""
    coordinator: TuyaCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Wait for first data fetch (safe no-op if another platform already did it)
    await coordinator.async_config_entry_first_refresh()

    entities: list[TuyaBinarySensorEntity] = []
    for device_id, device_data in coordinator.data.items():
        device_info = coordinator.devices.get(device_id, {})
        present_codes = {
            prop.get("code") for prop in device_data.get("properties", [])
        }

        for code, device_class in BINARY_SENSOR_MAP.items():
            if code not in present_codes:
                continue
            entities.append(
                TuyaBinarySensorEntity(
                    coordinator=coordinator,
                    device_id=device_id,
                    device_info_raw=device_info,
                    code=code,
                    device_class=device_class,
                )
            )

    async_add_entities(entities)


class TuyaBinarySensorEntity(CoordinatorEntity, BinarySensorEntity):
    """A boolean Tuya DPS property exposed as an HA binary sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TuyaCoordinator,
        device_id: str,
        device_info_raw: dict,
        code: str,
        device_class: Any,
    ) -> None:
        super().__init__(coordinator)

        self._device_id = device_id
        self._code = code

        self._attr_unique_id = f"{device_id}_{code}"
        self._attr_name = CODE_NAMES.get(code, code)
        self._attr_device_class = device_class

        device_name = device_info_raw.get("name", device_id)
        product_name = device_info_raw.get("product_name", "")
        category = device_info_raw.get("category", "")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            model=product_name or category,
            manufacturer="Tuya",
        )

    def _raw_value(self) -> Any | None:
        if self.coordinator.data is None:
            return None
        device_data = self.coordinator.data.get(self._device_id)
        if device_data is None:
            return None
        for prop in device_data.get("properties", []):
            if prop.get("code") == self._code:
                return prop.get("value")
        return None

    @property
    def is_on(self) -> bool | None:
        """Map the raw DPS value to on/off.

        Bools map directly; numbers are true when non-zero (fault bitmap);
        strings are true for "on"/"online"/"true"/"1".
        """
        raw = self._raw_value()
        if raw is None:
            return None
        if isinstance(raw, bool):
            return raw
        if isinstance(raw, (int, float)):
            return raw != 0
        if isinstance(raw, str):
            return raw.lower() in ("on", "online", "true", "1")
        return bool(raw)
