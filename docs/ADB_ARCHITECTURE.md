# ADB Engine & Device Monitoring Architecture

## ADB Engine

The `ADBEngine` class (`backend/app/services/adb_watcher/adb_engine.py`) provides enterprise-grade Android Debug Bridge control.

### Architecture

```
┌──────────────────────────────────────┐
│            ADBEngine (Singleton)      │
├──────────────────────────────────────┤
│  - Command Queue (asyncio.Queue)      │
│  - Device Locks (per-serial)          │
│  - Global Lock                        │
│  - Whitelist Validation               │
│  - Auto-reconnect                     │
│  - Timeout Handling                   │
└──────────────────────────────────────┘
```

### Features

- **Thread-safe execution** via asyncio locks per device
- **Command queue** with max size configuration
- **Command whitelist** prevents injection attacks
- **Auto-retry** with configurable attempts and delays
- **Timeout handling** per command with configurable timeout
- **Multi-device support** - isolated device locks
- **Health checking** - server status, device online state

### Key Methods

| Method | Description |
|--------|-------------|
| `start_server()` | Start ADB server, ensure queue worker |
| `stop_server()` | Kill ADB server, clear device cache |
| `restart_server()` | Stop + start with delay |
| `list_devices()` | Get connected devices with properties |
| `get_device_info(serial)` | Full device info + metrics |
| `is_online(serial)` | Check if device is reachable |
| `wait_for_device(serial, timeout)` | Block until device online |
| `shell(serial, cmd)` | Execute shell command (whitelisted) |
| `execute(serial, cmd)` | Execute ADB command (whitelisted) |
| `reconnect()` | Kill and restart ADB server |
| `health_check()` | Return server health status |

### Command Whitelist

All commands are validated against a whitelist before execution:

```python
shell:dumpsys telephony.registry
shell:dumpsys battery
shell:dumpsys power
shell:dumpsys connectivity
shell:getprop
shell:settings get secure android_id
shell:input keyevent KEYCODE_CALL
shell:input keyevent KEYCODE_ENDCALL
shell:input keyevent 5
shell:input keyevent 6
devices
devices -l
start-server
kill-server
get-state
wait-for-device
...
```

## Device Monitoring

### ADB Watcher Service

Monitors device connection changes:

1. Ensures ADB server is running
2. Polls device list periodically
3. Detects newly connected/disconnected devices
4. Publishes `DeviceConnectedEvent` / `DeviceDisconnectedEvent`
5. Tracks ADB server status changes

### Device Heartbeat Service

Periodic health checks on all connected devices:

1. Gets device info (battery, screen, charging, IP)
2. Updates device record in database
3. Stores metric snapshot in `device_metrics` table
4. Publishes `DeviceHeartbeatEvent` and `DeviceMetricsUpdatedEvent`

## Call Detection Flow

```
┌──────────────────┐
│ ADBEngine polls  │
│ dumpsys telephony│
│ every 1 second   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Parse mCallState │
│ 0=IDLE, 1=RING, │
│ 2=ACTIVE         │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ CallStateMachine │
│ Validate         │
│ transition       │
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
 Incoming   Call Ended
    │         │
    ▼         ▼
 CallerIdent  DB Update
    │
    ▼
 EventBus
 Publish
```

### State Machine Transitions

```
    IDLE ───► RINGING ───► ANSWERING ───► ACTIVE ───► ENDED
                │              │              │
                ├──► MISSED    └──► FAILED    └──► FAILED
                └──► ENDED
```

## Auto Answer Service

### Workflow

```
1. Incoming call detected (RINGING state)
2. `can_auto_answer()` checks:
   - AUTO_ANSWER_ENABLED setting
   - Device is online
3. Wait AUTO_ANSWER_DELAY_SECONDS
4. Attempt answer commands in sequence:
   - input keyevent KEYCODE_CALL
   - input keyevent 5
   - service call phone 0 s16 call
5. Verify state changed to ACTIVE
6. If failed, retry up to AUTO_ANSWER_RETRY_COUNT
7. Publish CallAnsweredEvent on success
```

## Event System

### Event Types

| Event | Publisher | Subscribers |
|-------|-----------|-------------|
| `device_connected` | ADB Watcher | WebSocket, DB |
| `device_disconnected` | ADB Watcher | WebSocket, DB |
| `heartbeat` | Heartbeat Service | WebSocket, DB |
| `incoming_call` | Call Detection | WebSocket, DB, Auto Answer |
| `call_answered` | Call Detection / Auto Answer | WebSocket, DB |
| `call_missed` | Call Detection | WebSocket, DB |
| `call_ended` | Call Detection | WebSocket, DB |
| `call_state_changed` | Call Detection | WebSocket |
| `adb_status_changed` | ADB Watcher | WebSocket |
| `device_metrics_updated` | Heartbeat Service | WebSocket |

## Real-Time WebSocket

The WebSocket manager broadcasts all events to connected clients.

### Client Connection

```
ws://localhost:8000/ws
```

### Message Format

```json
{
  "type": "event_type",
  "data": { ... },
  "timestamp": "2026-06-01T12:00:00Z"
}
```

### Heartbeat

Server sends `{"type": "ping"}` every 30 seconds.
Client should respond with `"ping"` text message.
