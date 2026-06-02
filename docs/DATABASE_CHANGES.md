# Database Changes (Phase 2)

## New Columns

### devices table

| Column | Type | Description |
|--------|------|-------------|
| `connection_type` | VARCHAR(50) | USB, WiFi, etc. |
| `usb_debugging_enabled` | BOOLEAN | USB debugging state |
| `adb_status` | VARCHAR(50) | ADB connection status |
| `heartbeat_at` | TIMESTAMPTZ | Last heartbeat timestamp |
| `last_command_at` | TIMESTAMPTZ | Last ADB command execution |
| `device_ip` | VARCHAR(50) | Device IP address |
| `battery_level` | INTEGER | Last known battery % |
| `charging` | BOOLEAN | Charging state |
| `screen_state` | VARCHAR(20) | Screen on/off/dream |

### call_sessions table

| Column | Type | Description |
|--------|------|-------------|
| `incoming_detected_at` | TIMESTAMPTZ | When call was detected |
| `answered_at` | TIMESTAMPTZ | When call was answered |
| `caller_type` | VARCHAR(50) | external/private/saved/unknown |
| `raw_call_data` | TEXT | Raw dumpsys data from detection |

## New Tables

### device_events

| Column | Type | Index |
|--------|------|-------|
| `id` | SERIAL PK | PRIMARY |
| `device_id` | INT FK → devices.id | YES |
| `event_type` | VARCHAR(100) | YES |
| `event_name` | VARCHAR(255) | |
| `event_data` | TEXT | |
| `event_time` | TIMESTAMPTZ | YES |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

Composite index: `(device_id, event_time)`

### device_metrics

| Column | Type | Index |
|--------|------|-------|
| `id` | SERIAL PK | PRIMARY |
| `device_id` | INT FK → devices.id | YES |
| `battery_level` | INTEGER | |
| `charging` | BOOLEAN | |
| `screen_state` | VARCHAR(20) | |
| `usb_connected` | BOOLEAN | |
| `signal_strength` | INTEGER | |
| `network_type` | VARCHAR(50) | |
| `cpu_usage` | FLOAT | |
| `memory_usage` | FLOAT | |
| `captured_at` | TIMESTAMPTZ | YES |

Composite index: `(device_id, captured_at)`

### adb_commands

| Column | Type | Index |
|--------|------|-------|
| `id` | SERIAL PK | PRIMARY |
| `device_id` | INT FK → devices.id | YES |
| `command` | VARCHAR(500) | |
| `command_type` | VARCHAR(50) | |
| `status` | VARCHAR(20) | pending/success/failed/timeout |
| `execution_time` | FLOAT | |
| `response` | TEXT | |
| `error_message` | TEXT | |
| `executed_at` | TIMESTAMPTZ | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

Composite index: `(device_id, executed_at)`

## Relationships

```
devices
  ├── 1──* device_events
  ├── 1──* device_metrics
  ├── 1──* adb_commands
  └── 1──* call_sessions
```
