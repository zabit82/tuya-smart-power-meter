# Tuya Power Meter

[🇷🇺 Русская документация](README.ru.md)

A Go CLI application that connects to the [Tuya OpenAPI](https://openapi.tuyaeu.com), authenticates using your Client ID & Client Secret, fetches device data, and displays it as a structured table in the terminal.

## Features

- 🔑 Secure HMAC-SHA256 authentication (no third-party auth libraries)
- 📋 Lists all devices linked to your cloud project
- ⚡ Fetches live device status (DPS — data points)
- 🗂️ Renders everything as clean tables in the terminal
- 🔍 Optionally query specific devices by ID

## Prerequisites

1. A [Tuya Developer](https://iot.tuya.com) account
2. A cloud project with your devices linked to it
3. Your **Client ID** (Access ID) and **Client Secret** (Access Secret) from the project overview

## Usage

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `TUYA_CLIENT_ID` | ✅ | Your Access ID from the Tuya developer portal |
| `TUYA_CLIENT_SECRET` | ✅ | Your Access Secret |
| `TUYA_DEVICE_IDS` | ❌ | Comma-separated device IDs (if empty, fetches all devices) |
| `TUYA_API_HOST` | ❌ | API host (default: `https://openapi.tuyaeu.com`) |

### Run

```bash
export TUYA_CLIENT_ID=your_client_id
export TUYA_CLIENT_SECRET=your_client_secret

# Optionally filter specific devices:
# export TUYA_DEVICE_IDS=device_id_1,device_id_2

go run .
```

### Build

```bash
go build -o tuya-meter .
./tuya-meter
```

## Output Example

```
🔌  Connecting to https://openapi.tuyaeu.com...
🔑  Obtaining access token...
✅  Authenticated successfully.

🔍  Fetching all devices from project...
   Found 2 device(s).

📋  DEVICES
+------------------+----------------------+--------+----------+-------------------+---------------------+
| NAME             | ID                   | ONLINE | CATEGORY | PRODUCT NAME      | LAST UPDATE         |
+------------------+----------------------+--------+----------+-------------------+---------------------+
| Living Room Plug | bf1234567890abcdef01 | ✅ yes  | cz       | Smart Plug 16A    | 2026-03-06 12:00:00 |
| Kitchen Meter    | bf1234567890abcdef02 | ✅ yes  | dlq      | Power Meter       | 2026-03-06 11:59:01 |
+------------------+----------------------+--------+----------+-------------------+---------------------+

⚡  STATUS — LIVING ROOM PLUG
+------------------+-------+---------+
| CODE             | VALUE | TYPE    |
+------------------+-------+---------+
| switch_1         | true  | Boolean |
| cur_power        | 1234  | Integer |
| cur_voltage      | 2298  | Integer |
| cur_current      | 541   | Integer |
+------------------+-------+---------+
```

## Project Structure

```
.
├── main.go           # Entry point, config, orchestration
├── tuya/
│   ├── client.go     # API client, auth, request signing
│   └── models.go     # API response types
└── render/
    └── render.go     # Terminal table rendering
```

## API Endpoints Used

| Endpoint | Purpose |
|---|---|
| `GET /v1.0/token?grant_type=1` | Obtain access token |
| `GET /v1.0/iot-03/devices` | List all project devices |
| `GET /v1.0/devices/{id}` | Get single device info |
| `GET /v2.0/cloud/thing/{id}/shadow/properties` | Get live device DPS values |
| `GET /v2.0/cloud/thing/{id}/model` | Get property specs (scale/unit) |

---

## Home Assistant Integration

A full Home Assistant custom component is included in `custom_components/tuya_power_meter/`.

### Features

- ✅ Setup via UI (**Settings → Integrations → Add Integration → Tuya Power Meter**)
- ✅ Sensors with correct `device_class` (power, voltage, current, energy, temperature)
- ✅ Scaled values with units (e.g. `286.6 W`, `236.1 V`, `1.569 A`)
- ✅ Configurable poll interval (default 30 s)
- ✅ Auto token refresh
- ✅ All devices grouped under their own device entry in HA

### Installation

**Option A — HACS Custom Repository** _(recommended)_
1. In HACS → Custom Repositories → add this repo URL → category **Integration**
2. Install "Tuya Power Meter" → restart HA

**Option B — Manual**
```bash
# From the repo root:
cp -r custom_components/tuya_power_meter  /config/custom_components/
# Restart Home Assistant
```

### Configuration

1. Go to **Settings → Integrations → + Add Integration**
2. Search for **Tuya Power Meter**
3. Enter your **Access ID** and **Access Secret**
4. Enter your **Device IDs** (comma-separated, e.g. `bf52363ad6fdd994694spp,bf67807215b610d682sdis`)
5. Choose a **poll interval** (10–3600 s, default 30 s)

### Resulting Entities (example)

| Entity | Value | Unit | Device class |
|---|---|---|---|
| `sensor.single_digital_meter_cur_power1` | 286.6 | W | power |
| `sensor.single_digital_meter_cur_voltage1` | 236.1 | V | voltage |
| `sensor.single_digital_meter_cur_current1` | 1.569 | A | current |
| `sensor.single_digital_meter_total_energy1` | 18997.041 | kWh | energy |
| `sensor.ac_charging_pile_devicekw` | 6.2 | kW | power |
| `sensor.ac_charging_pile_a_voltage` | 212 | V | voltage |
| `sensor.ac_charging_pile_devicetemp` | 33.1 | °C | temperature |
