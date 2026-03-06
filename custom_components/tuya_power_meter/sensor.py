"""Sensor platform for Tuya Power Meter."""
from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CODE_MAP, CONF_CLIENT_ID, DOMAIN
from .coordinator import TuyaCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tuya Power Meter sensors from a config entry."""
    coordinator: TuyaCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Wait for first data fetch before creating entities
    await coordinator.async_config_entry_first_refresh()

    entities: list[TuyaSensorEntity] = []
    for device_id, device_data in coordinator.data.items():
        device_info = coordinator.devices.get(device_id, {})
        specs = device_data.get("specs", {})

        for prop in device_data.get("properties", []):
            code = prop.get("code", "")
            if not code:
                continue

            spec = specs.get(code, {})
            entities.append(
                TuyaSensorEntity(
                    coordinator=coordinator,
                    device_id=device_id,
                    device_info_raw=device_info,
                    code=code,
                    spec=spec,
                    prop_type=prop.get("type", spec.get("type", "")),
                )
            )

    async_add_entities(entities)


def _resolve_device_class(
    code: str,
) -> tuple[SensorDeviceClass | None, SensorStateClass | None]:
    """Map a DPS code to an HA device_class and state_class."""
    for entry in CODE_MAP:
        for pattern in entry["patterns"]:
            if pattern.lower() in code.lower():
                return entry["device_class"], entry["state_class"]
    return None, None


def _apply_scale(value: Any, scale: float, prop_type: str) -> Any:
    """Apply scale factor for numeric values."""
    if prop_type == "value" and isinstance(value, (int, float)) and scale > 0:
        divisor = math.pow(10, scale)
        result = value / divisor
        # Round to the number of decimal places implied by scale
        decimals = int(scale)
        return round(result, decimals)
    if isinstance(value, bool):
        return value
    # Integers reported as floats by JSON parser
    if isinstance(value, float) and value == int(value):
        return int(value)
    return value


class TuyaSensorEntity(CoordinatorEntity, SensorEntity):
    """A single Tuya DPS property exposed as an HA sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TuyaCoordinator,
        device_id: str,
        device_info_raw: dict,
        code: str,
        spec: dict,
        prop_type: str,
    ) -> None:
        super().__init__(coordinator)

        self._device_id = device_id
        self._code = code
        self._spec = spec
        self._prop_type = prop_type

        # Entity identification
        self._attr_unique_id = f"{device_id}_{code}"

        # Human-readable name — use spec name if available, else code
        spec_name = spec.get("name", "")
        self._attr_name = spec_name if spec_name else code

        # Unit of measurement from model spec
        unit = spec.get("unit", "")
        self._attr_native_unit_of_measurement = unit if unit else None

        # device_class and state_class by code pattern
        device_class, state_class = _resolve_device_class(code)
        self._attr_device_class = device_class
        self._attr_state_class = state_class

        # Device grouping in HA device registry
        device_name = device_info_raw.get("name", device_id)
        product_name = device_info_raw.get("product_name", "")
        category = device_info_raw.get("category", "")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            model=product_name or category,
            manufacturer="Tuya",
        )

    @property
    def _current_value(self) -> Any | None:
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
    def native_value(self) -> Any | None:
        raw = self._current_value
        if raw is None:
            return None
        scale = self._spec.get("scale", 0.0)
        return _apply_scale(raw, scale, self._prop_type)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose raw value and dp_id as extra attributes."""
        attrs: dict[str, Any] = {"code": self._code}
        if self.coordinator.data:
            device_data = self.coordinator.data.get(self._device_id, {})
            for prop in device_data.get("properties", []):
                if prop.get("code") == self._code:
                    attrs["raw_value"] = prop.get("value")
                    attrs["dp_id"] = prop.get("dp_id")
                    ts_ms = prop.get("time", 0)
                    if ts_ms:
                        # Convert ms → s if necessary
                        ts = ts_ms // 1000 if ts_ms > 1e12 else ts_ms
                        attrs["last_changed_ts"] = ts
                    break
        return attrs
