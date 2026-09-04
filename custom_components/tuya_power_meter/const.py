"""Constants for the Tuya Power Meter integration."""
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

DOMAIN = "tuya_power_meter"

DEFAULT_HOST = "https://openapi.tuyaeu.com"
DEFAULT_POLL_INTERVAL = 30  # seconds

CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_DEVICE_IDS = "device_ids"
CONF_API_HOST = "api_host"
CONF_POLL_INTERVAL = "poll_interval"

# Map DPS code patterns to HA device_class and state_class.
# Order matters — first match wins.
CODE_MAP = [
    # Energy totals (lifetime cumulative) — total increasing.
    # Checked FIRST: "DeviceKw" (power) is a substring of "DeviceKwh" (energy),
    # so energy must win to avoid misclassifying the lifetime counter as power.
    {
        "patterns": ["total_energy", "DeviceKwh", "kwh"],
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    # Accumulated energy counters (true cumulative) — total increasing
    {
        "patterns": ["acc_energy"],
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    # Per-session / remaining energy (resets each charge or decreases) — measurement.
    # NOT total_increasing: that would corrupt HA energy statistics.
    {
        "patterns": ["charge_energy_once", "balance_energy"],
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    # Energy deltas / additions — measurement
    {
        "patterns": ["energy_add", "add_ele"],
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    # Power (W or kW)
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
    # Temperature
    {
        "patterns": ["DeviceTemp", "temperature", "temp"],
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
]

# DPS codes never exposed as sensors: raw payloads without a usable value,
# empty strings, and write-only commands.
EXCLUDE_CODES = {
    "alarm_set_1",
    "alarm_set_2",
    "system_version",
    "clear_energy",        # write-only "clear counter" command
    "ChargingOperation",   # write-only command
    "IDVerificationSet",   # setup flag, not a live state
}

# DPS codes exposed but disabled by default (control/setup parameters and
# unused probes). The user can enable them in the entity registry.
DEFAULT_DISABLED_CODES = {
    "Set16A", "Set32A", "Set40A", "Set50A", "set60a", "set80a",
    "DeviceMaxSetA",
    "SetDelayTime", "SetDefineTime",
    "Ctime", "CTime2",
    "DeviceTemp2",  # second probe, usually reports -30.0 °C (unused)
}

# Curated human-readable English names for common Tuya EV-charger DPS codes.
# Used instead of the (often Chinese) model spec name so entity_ids stay
# clean and readable. Falls back gracefully for unknown codes.
CODE_NAMES = {
    "work_state": "Charging state",
    "work_mode": "Work mode",
    "fault": "Fault",
    "switch": "Charging switch",
    "online_state": "Online state",
    "DeviceState": "Device state",
    "PhaseFlag": "Phase mode",
    "balance_energy": "Remaining energy",
    "charge_energy_once": "Charge energy (session)",
    "A_Voltage": "Phase A voltage",
    "B_Voltage": "Phase B voltage",
    "C_Voltage": "Phase C voltage",
    "A_Current": "Phase A current",
    "B_Current": "Phase B current",
    "C_Current": "Phase C current",
    "DeviceKw": "Power",
    "DeviceTemp": "Temperature",
    "DeviceTemp2": "Temperature 2",
    "DeviceKwh": "Total energy",
    "RFID": "RFID card",
}

# Boolean/status DPS codes exposed as binary sensors (code -> device_class).
# None = generic binary sensor. These are excluded from the sensor platform
# to avoid duplicate entities.
BINARY_SENSOR_MAP = {
    "switch": None,                              # on = charging enabled
    "fault": BinarySensorDeviceClass.PROBLEM,    # on = fault present (bitmap != 0)
    "online_state": BinarySensorDeviceClass.CONNECTIVITY,  # on = "online"
    "RFID": None,                                # on = RFID card present
}
