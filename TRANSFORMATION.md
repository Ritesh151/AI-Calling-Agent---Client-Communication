# Enterprise Platform Transformation — AI Call Reception System

## 1. Root Cause (Phase 1)

**Symptom:** Dashboard showed `Connected Devices = 1` and `Total Devices = 1` with no physical Android device attached.

**Primary root cause:** Device connection state was **written to PostgreSQL when ADB reported a device online, but never cleared when ADB stopped reporting it**. The dashboard reads `is_connected` from the database via `/api/v1/devices` and `/api/v1/devices/connected`, so stale rows appeared as live connections.

**Contributing factors:**

| Layer | Issue |
|-------|--------|
| `DeviceHeartbeatService` | Only updated online devices; no reconciliation for absent serials |
| `DeviceStatusService` | Same one-way update pattern |
| `ADBWatcherService` | Detected disconnect and published events but **did not update DB** |
| `EventDispatcherWorker` | Forwarded events to WebSocket only |
| Cold start | `_known_devices = {}` — no startup sync against DB |
| Frontend dashboard | Used stale `connectedDevices` store slice; **no WebSocket** on main dashboard |
| Interval | Heartbeat ran every **30s** (now **5s**) |

**Note:** Stack uses **PostgreSQL + SQLAlchemy**, not MongoDB.

---

## 2. Broken Files (with line references)

| File | Lines | Problem |
|------|-------|---------|
| `backend/app/services/device_heartbeat/heartbeat_service.py` | 52–78, 80–114 | Sets `is_connected=True`; never disconnects missing devices |
| `backend/app/services/device_status.py` | 43–71 | Heartbeat loop updates only devices returned by ADB |
| `backend/app/services/adb_watcher/adb_watcher_service.py` | 100–110 | `_handle_device_disconnected` publishes event only |
| `backend/app/repositories/device_repository.py` | 25–30 | `get_connected_devices()` trusts stale `is_connected` flag |
| `backend/app/repositories/base.py` | 44–47 | Previously skipped `is_connected=False` when value treated as falsy edge case |
| `backend/app/core/config.py` | 93 | `DEVICE_HEARTBEAT_INTERVAL_SECONDS = 30` |
| `frontend/src/app/dashboard/page.tsx` | 13–24 | Used `connectedDevices.length` without live ADB sync / WebSocket |
| `frontend/src/hooks/use-devices.ts` | 11–32 | No periodic refresh; connected query decoupled from truth |

---

## 3. Code Changes (Phase 2–3)

### New

- `backend/app/services/device_sync.py` — **ADB-as-source-of-truth** reconciliation every cycle
- `backend/app/db/models/project_management.py` — Project → Milestone → Sprint → Task → Subtask hierarchy
- `backend/app/services/ai_agents/*` — Coordinator, Client Manager, CTO, QA agents
- `backend/app/api/v1/projects.py` — Project & agent APIs

### Modified

- `DeviceHeartbeatService` — calls `DeviceSyncService.sync()` each 5s before metrics
- `devices.py` API — `POST /devices/sync`, auto-sync on `GET /devices` and `GET /devices/connected`
- `main.py` — startup device sync
- `event_types.py` — `DevicesSyncedEvent`
- `config.py` — heartbeat interval **5 seconds**
- Frontend dashboard, `use-devices`, `use-websocket`, dashboard layout

---

## 4. New Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Dashboard (Next.js)                          │
│  useWebSocket ←→ useDevices (5s poll + invalidation on events)    │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST + WS
┌────────────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend                               │
│  ┌──────────────┐  ┌─────────────────┐  ┌──────────────────┐   │
│  │ Device API   │→ │ DeviceSyncService│← │ ADBEngine        │   │
│  │ (sync first) │  │ (adb devices -l) │  │ (single truth)   │   │
│  └──────────────┘  └────────┬─────────┘  └──────────────────┘   │
│                             │                                    │
│  ┌──────────────┐  ┌────────▼─────────┐  ┌──────────────────┐   │
│  │ Heartbeat    │→ │ PostgreSQL       │  │ EventBus → WS    │   │
│  │ Worker (5s)  │  │ devices table    │  │ device_* events  │   │
│  └──────────────┘  └──────────────────┘  └──────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ AI Agents: Coordinator | Client Manager | CTO | QA        │   │
│  │ Project hierarchy + bug_reports + agent_conversations     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Device status rules (ADB → DB)

| ADB state | DB `status` | `is_connected` |
|-----------|-------------|----------------|
| `device` | `connected` | `true` |
| `unauthorized` | `unauthorized` | `false` |
| `offline` | `offline` | `false` |
| absent from list | `disconnected` | `false` |

---

## 5. Database Changes

New tables (auto-created via `Base.metadata.create_all`):

- `projects`, `milestones`, `sprints`, `project_tasks`, `project_subtasks`
- `bug_reports`, `agent_conversations`, `audit_logs`

Existing `devices` table: no migration required; logic fixes stale `is_connected` values.

---

## 6. Socket Changes

| Event | When |
|-------|------|
| `device_connected` | Serial appears online |
| `device_disconnected` | Serial removed or state ≠ device |
| `devices_synced` | After each reconciliation (counts in `data`) |
| `heartbeat` / call events | Unchanged |

Frontend invalidates `["devices"]` and `["devices", "connected"]` on sync/disconnect events.

---

## 7. ADB Changes

- `DeviceSyncService` runs `adb devices -l` via `ADBEngine.list_devices()`
- Runs on: API read (optional `?sync=true`), heartbeat worker (5s), server startup
- If ADB server down: all DB devices marked disconnected

---

## 8. Frontend Changes

- Dashboard counts from `devices.filter(d => d.is_connected)`
- `useWebSocket()` in dashboard layout (global real-time)
- `useDevices` 5s `refetchInterval` + dual query refetch
- `devices_synced` WebSocket handler
- `POST /devices/sync` client method

---

## 9. AI Agent Modules

| Agent | Path | API |
|-------|------|-----|
| Project Coordinator | `services/ai_agents/coordinator.py` | `POST /api/v1/projects/agents/coordinator/chat` |
| Client Manager | `services/ai_agents/client_manager.py` | `POST /api/v1/projects/agents/client/chat` |
| CTO | `services/ai_agents/cto_agent.py` | `POST /api/v1/projects/agents/cto/chat` |
| QA | `services/ai_agents/qa_agent.py` | `POST /api/v1/projects/agents/qa/scan` |

Set `AI_ANALYSIS_API_KEY` for full LLM responses; otherwise structured fallback JSON is returned.

---

## 10. Security Improvements

| Item | Status |
|------|--------|
| JWT auth on REST | Existing |
| Rate limiting | Existing middleware |
| WebSocket auth message | Frontend sends token; **server validation TODO** |
| Audit logs model | Added (`audit_logs` table) |
| RBAC on admin routes | Existing `require_role` |
| Request validation | Pydantic on new endpoints |

---

## 11. Testing Strategy

```bash
# 1. Verify ADB truth
adb devices -l

# 2. Sync API (with auth token)
curl -X POST http://localhost:8000/api/v1/devices/sync -H "Authorization: Bearer $TOKEN"

# 3. List devices — should show connected_count=0 when unplugged
curl http://localhost:8000/api/v1/devices -H "Authorization: Bearer $TOKEN"

# 4. QA agent scan
curl -X POST "http://localhost:8000/api/v1/projects/agents/qa/scan" -H "Authorization: Bearer $TOKEN"

# 5. Backend unit tests
cd backend && pytest tests/ -v
```

**Manual:** Plug/unplug USB device; dashboard counts should update within 5s without refresh.

---

## 12. Deployment Strategy

1. Deploy backend with ADB accessible on host (USB or `adb connect`)
2. Set `DEVICE_HEARTBEAT_INTERVAL_SECONDS=5` in `.env`
3. Run `Base.metadata.create_all` (startup) for new project tables
4. Deploy frontend with `NEXT_PUBLIC_WS_URL=ws://<api-host>/ws`
5. Run QA scan post-deploy: `POST /projects/agents/qa/scan`

---

## 13. Production Checklist

- [ ] `adb` installed on server; udev rules for device permissions
- [ ] `AI_ANALYSIS_API_KEY` set for autonomous agents
- [ ] `JWT_SECRET_KEY` rotated from default
- [ ] PostgreSQL + Redis healthy (`/health/database`, `/health/redis`)
- [ ] `/health/devices` shows `connected_devices: 0` when unplugged
- [ ] WebSocket reachable through reverse proxy (Upgrade headers)
- [ ] Sentry/monitoring wired (`SENTRY_DSN`)
- [ ] Log rotation enabled (`LOG_FILE_*`)
- [ ] Rate limits tuned for production traffic

---

## Quick verification after deploy

```bash
./verify_system.sh
adb devices -l   # expect empty list when unplugged
# Dashboard should show Connected Devices: 0, Total Devices: N (registered history)
```
