# Tuya Power Meter

Go CLI приложение, которое подключается к [Tuya OpenAPI](https://openapi.tuyaeu.com), аутентифицируется с помощью Client ID и Client Secret, получает данные с устройств и отображает их в виде структурированных таблиц в терминале.

## Возможности

- 🔑 Безопасная аутентификация HMAC-SHA256 (без сторонних библиотек)
- 📋 Список всех устройств, привязанных к облачному проекту
- ⚡ Получение актуального статуса устройств (DPS — точки данных)
- 🗂️ Вывод всего в виде красивых таблиц в терминале
- 🔍 Возможность запросить конкретные устройства по ID

## Требования

1. Аккаунт на [Tuya Developer](https://iot.tuya.com)
2. Облачный проект с привязанными устройствами
3. **Client ID** (Access ID) и **Client Secret** (Access Secret) из обзора проекта

## Использование

### Переменные окружения

| Переменная | Обязательная | Описание |
|---|---|---|
| `TUYA_CLIENT_ID` | ✅ | Access ID с портала разработчика Tuya |
| `TUYA_CLIENT_SECRET` | ✅ | Access Secret |
| `TUYA_DEVICE_IDS` | ❌ | ID устройств через запятую (если не указано — загружает все) |
| `TUYA_API_HOST` | ❌ | API хост (по умолчанию: `https://openapi.tuyaeu.com`) |

### Запуск

```bash
export TUYA_CLIENT_ID=ваш_client_id
export TUYA_CLIENT_SECRET=ваш_client_secret

# Опционально — только конкретные устройства:
# export TUYA_DEVICE_IDS=device_id_1,device_id_2

go run .
```

### Сборка

```bash
go build -o tuya-meter .
./tuya-meter
```

## Пример вывода

```
🔌  Connecting to https://openapi.tuyaeu.com...
🔑  Obtaining access token...
✅  Authenticated successfully.

🔍  Fetching all devices from project...
   Found 2 device(s).

📋  DEVICES
+----------------------+------------------------+--------+----------+----------------------+---------------------+
|         NAME         |           ID           | ONLINE | CATEGORY |     PRODUCT NAME     |     LAST UPDATE     |
+----------------------+------------------------+--------+----------+----------------------+---------------------+
| Single Digital Meter | bf52363ad6fdd994694spp | ✅ yes | cz       | Single Digital Meter | 2026-03-06 04:32:00 |
| AC charging pile     | bf67807215b610d682sdis | ✅ yes | qccdz    | AC charging pile     | 2026-03-06 14:54:42 |
+----------------------+------------------------+--------+----------+----------------------+---------------------+

⚡  STATUS — SINGLE DIGITAL METER
+-------------------+-------------------+-----------+------+-------+----------------+
|       CODE        |       NAME        |   VALUE   | UNIT | TYPE  |  LAST UPDATE   |
+-------------------+-------------------+-----------+------+-------+----------------+
| cur_power1        | 当前功率          | 287.3     | W    | value | 03-06 15:37:03 |
| cur_current1      | 当前电流          | 1.569     | A    | value | 03-06 15:37:03 |
| cur_voltage1      | 当前电压          | 236.1     | V    | value | 03-06 15:37:03 |
| total_energy1     | 总电量            | 18997.041 | kwh  | value | 03-06 15:37:03 |
| today_acc_energy1 | 今日用电量        | 4.679     | kwh  | value | 03-06 15:37:03 |
+-------------------+-------------------+-----------+------+-------+----------------+
```

## Структура проекта

```
.
├── main.go                          # Точка входа, конфигурация
├── tuya/
│   ├── client.go                    # API клиент, аутентификация, подпись запросов
│   └── models.go                    # Типы ответов API
├── render/
│   └── render.go                    # Вывод таблиц в терминале
└── custom_components/
    └── tuya_power_meter/            # Интеграция для Home Assistant
```

## Используемые API эндпоинты

| Эндпоинт | Назначение |
|---|---|
| `GET /v1.0/token?grant_type=1` | Получение токена доступа |
| `GET /v1.0/iot-03/devices` | Список всех устройств проекта |
| `GET /v1.0/devices/{id}` | Информация об устройстве |
| `GET /v2.0/cloud/thing/{id}/shadow/properties` | Актуальные значения DPS |
| `GET /v2.0/cloud/thing/{id}/model` | Спецификация свойств (масштаб/единицы) |

---

## Интеграция с Home Assistant

Полный custom component для Home Assistant находится в `custom_components/tuya_power_meter/`.

### Возможности

- ✅ Настройка через UI (**Настройки → Интеграции → Добавить интеграцию → Tuya Power Meter**)
- ✅ Сенсоры с правильными `device_class` (мощность, напряжение, ток, энергия, температура)
- ✅ Масштабированные значения с единицами (например, `286.6 W`, `236.1 V`, `1.569 A`)
- ✅ Настраиваемый интервал опроса (по умолчанию 30 с)
- ✅ Автоматическое обновление токена
- ✅ Каждое устройство группируется в отдельную карточку устройства в HA

### Установка

**Вариант А — HACS (рекомендуется)**
1. В HACS → Пользовательские репозитории → добавить URL этого репозитория → категория **Интеграция**
2. Установить «Tuya Power Meter» → перезапустить HA

**Вариант Б — Вручную**
```bash
# Из корня репозитория:
cp -r custom_components/tuya_power_meter /config/custom_components/
# Перезапустить Home Assistant
```

### Настройка

1. Перейти в **Настройки → Интеграции → + Добавить интеграцию**
2. Найти **Tuya Power Meter**
3. Ввести **Access ID** и **Access Secret**
4. Ввести **Device IDs** через запятую (например, `bf52363ad6fdd994694spp,bf67807215b610d682sdis`)
5. Выбрать **интервал опроса** (10–3600 с, по умолчанию 30 с)

### Создаваемые сущности (пример)

| Сущность | Значение | Единица | Device class |
|---|---|---|---|
| `sensor.single_digital_meter_cur_power1` | 286.6 | W | power |
| `sensor.single_digital_meter_cur_voltage1` | 236.1 | V | voltage |
| `sensor.single_digital_meter_cur_current1` | 1.569 | A | current |
| `sensor.single_digital_meter_total_energy1` | 18997.041 | kWh | energy |
| `sensor.ac_charging_pile_devicekw` | 6.2 | kW | power |
| `sensor.ac_charging_pile_a_voltage` | 212 | V | voltage |
| `sensor.ac_charging_pile_devicetemp` | 33.1 | °C | temperature |
