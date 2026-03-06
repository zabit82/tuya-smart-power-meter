# Tuya Power Meter

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
| `GET /v1.0/devices/{id}/status` | Get device DPS status |
