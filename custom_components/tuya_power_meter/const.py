"""Constants for the Tuya Power Meter integration."""
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

DOMAIN = "tuya_power_meter"

DEFAULT_HOST = "https://openapi.tuyaeu.com"
DEFAULT_POLL_INTERVAL = 30  # seconds

CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_DEVICE_IDS = "device_ids"
CONF_API_HOST = "api_host"
CONF_POLL_INTERVAL = "poll_interval"

# Map DPS code patterns to HA device_class and state_class
# Order matters — first match wins
CODE_MAP = [
    # Power  (W or kW)
    {
        "patterns": ["cur_power", "DeviceKw", "power"],
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    # Voltage
    {
        "patterns": ["cur_voltage", "Voltage", "voltage"],
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    # Current (A)
    {
        "patterns": ["cur_current", "Current", "current"],
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    # Energy totals (kWh) — total increasing
    {
        "patterns": ["total_energy", "DeviceKwh", "kwh"],
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    # Energy accumulations (today etc.) — total increasing
    {
        "patterns": ["acc_energy", "charge_energy_once", "balance_energy"],
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    # Energy additions (deltas) — measurement
    {
        "patterns": ["energy_add", "add_ele"],
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    # Temperature
    {
        "patterns": ["DeviceTemp", "temperature", "temp"],
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
]
