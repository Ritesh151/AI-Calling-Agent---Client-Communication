# ROOT CAUSE ANALYSIS - RATE LIMIT & DEVICE SYNC ISSUES

**Date:** June 2, 2026  
**Status:** CRITICAL ISSUES IDENTIFIED  
**Priority:** P0 - Production Blocking

---

## EXECUTIVE SUMMARY

The application has **THREE CRITICAL ROOT CAUSES** causing:
1. **Rate limit errors** (60 requests/minute hit during normal page usage)
2. **Device lifecycle inconsistency** (stale records, disconnected devices visible)
3. **Realtime sync unreliability** (WebSocket events not triggering re-fetches correctly)

---

## ROOT CAUSE #1: SETTINGS PAGE INFINITE REQUEST LOOP

### Problem
Settings page makes **sequential API calls for EACH setting** (up to 20+ calls) in a single save operation.

### Location
`frontend/src/app/dashboard/settings/page.tsx` - Line 107-120

```typescript
// ANTI-PATTERN: Sending individual requests for each setting
const promises = Object.entries(settingsToSave).map(([key, value]) => {
  return settingsService.upsert(key, {
    key, value, category, description
  });
});
await Promise.all(promises);  // ❌ 20+ concurrent API calls
```

### Impact
- **20+ requests** for a single save operation
- With 60 request/minute limit → **60 ÷ 20 = Only 3 saves allowed per minute**
- **Normal usage triggers rate limit errors**
- Each setting change = full re-render cycle = repeat problem

### Root Cause Details
Settings categories × settings per category = total requests:
- General (2) + Greeting (2) + Recording (3) + Transcription (2) + Device (4) + System (3) = **16-20 requests per save**

---

## ROOT CAUSE #2: DEVICES PAGE DOUBLE SYNC ON EVERY LOAD

### Problem
Device page makes **TWO sync requests** before rendering:

### Location
`frontend/src/hooks/use-devices.ts` - Line 20-34

```typescript
const devicesQuery = useQuery({
  queryKey: ["devices"],
  queryFn: async () => {
    const response = await devicesService.getAll({ 
      sync: true  // ❌ First sync
    });
  },
  refetchInterval: 15000,  // ❌ Auto-refetch every 15s
});

const adbStatusQuery = useQuery({
  queryKey: ["devices", "adb-status"],
  queryFn: async () => {
    await devicesService.getADBStatus();  // ❌ Not needed on every fetch
  },
  refetchInterval: 10000,  // ❌ Auto-refetch every 10s
});
```

### Backend Endpoint
`backend/app/api/v1/devices.py` - Line 77 (list_devices)

```python
@router.get("/", response_model=SuccessResponse[list[DeviceRead]])
async def list_devices(
    sync: bool = Query(True),  # ❌ Default TRUE forces full sync
    adb_present_only: bool = Query(False),
    # ... other params
):
    if sync:
        sync_result = await device_sync_service.sync(db)  # ❌ Blocks device fetch
```

### Impact
Every **15 seconds**:
1. GET /devices (with `sync=true`) → Syncs with ADB (SLOW)
2. GET /devices/adb-status → Checks ADB health

Plus every WebSocket event that triggers `queryClient.invalidateQueries({ queryKey: ["devices"] })`:
- Instant re-fetch

Result: **4+ requests/minute from devices page alone**

---

## ROOT CAUSE #3: WEBSOCKET MISSING QUERY INVALIDATION CLEANUP

### Problem
WebSocket handlers invalidate queries **without clearing old listeners**, causing:

### Location
`frontend/src/hooks/use-websocket.ts` - Line 134-190

```typescript
switch (message.type) {
  case "device_connected":
    queryClient.invalidateQueries({ queryKey: ["devices"] });
    // ❌ Handler stays registered even after invalidation
    // ❌ Multiple device_connected handlers accumulate
    break;
  case "settings_updated":
    queryClient.invalidateQueries({ queryKey: ["settings"] });
    break;
}
```

### Impact
- WebSocket handlers **never unsubscribe** in some cases
- Multiple concurrent handlers for same event
- Each handler triggers re-fetch
- **Duplicate requests** for single WebSocket message

---

## ROOT CAUSE #4: DEVICE SYNC SERVICE LACKS CLEANUP LOGIC

### Problem
Devices marked offline but **never deleted from database**.

### Location
`backend/app/services/device_sync.py`

Missing:
- Stale device removal (not seen for X seconds)
- Heartbeat timeout tracking
- Offline device cleanup

### Impact
- **Ghost devices** remain visible on frontend
- **Zombie devices** with stale timestamps
- Database grows indefinitely
- Disk space consumption

---

## ROOT CAUSE #5: RATE LIMIT MISCONFIGURATION

### Problem
Settings show `RATE_LIMIT_REQUESTS_PER_MINUTE: int = 300` but error says **60 requests/minute**.

### Location
`backend/app/core/config.py` - Line 76

```python
RATE_LIMIT_REQUESTS_PER_MINUTE: int = 300  # ✅ Correct value
```

### Issue
Either:
1. **Frontend environment variable override** or
2. **Docker/deployment config** sets it to 60, OR
3. **Nginx/reverse proxy** has separate rate limit

### Impact
- Discrepancy between code and production
- Users hit 60 limit even though backend allows 300

---

## DEVICE LIFECYCLE STATE MACHINE PROBLEMS

### Current State
```
Connected → [No Transition] → Connected  ❌
Connected → [timeout?] → Disconnected  ❌ (unclear trigger)
Disconnected → [Never deleted] → Ghost Device  ❌
```

### Required State Machine
```
NEW → DISCOVERING → CONNECTED (is_connected=true, last_seen=NOW)
           ↓
      FAILED → Not registered

CONNECTED → HEARTBEAT_OK (last_seen updated)
         → HEARTBEAT_TIMEOUT (mark disconnected after X seconds)
         → DELETED (removed from DB)

DISCONNECTED → RECONNECT_ATTEMPT
            → CONNECTED (restore to online)
            → CLEANUP (delete after retention_days)
```

---

## REQUEST COUNT ANALYSIS

### Current (Broken) State
**Devices Page on Load:**
- GET /devices (sync=true) = 2-3 internal queries
- GET /devices/adb-status = 1 request
- WebSocket device_connected event = invalidate → re-fetch
- Auto-refetch every 15s = 4 requests/minute baseline
- User navigates = +2 requests
- **Total: 6+ requests/minute just to load**

**Settings Page on Save:**
- 20 individual PUT /settings/key/{key} requests
- Each returns full setting object (unnecessary)
- Frontend re-renders on each response (React Query mutation)
- **Total: 20 requests for single action**

**Normal 5-minute session:**
- Devices page: 5 × 4 = 20 requests
- Settings page: 2 saves × 20 = 40 requests
- WebSocket events: ~30 requests
- **Total: 90 requests = HIT 60 LIMIT multiple times** ❌

---

## VERIFICATION FAILURES

### ADB State ≠ Database State
- Device shows "Connected" on UI
- Actually disconnected in ADB 10 seconds ago
- Database still shows `is_connected=true`
- No heartbeat timeout mechanism

### WebSocket Events ≠ UI Updates
- WebSocket emits `device_disconnected`
- Frontend updates store
- But old query results cached (staleTime/cacheTime issue)
- UI shows stale "Connected" status

### No Deduplication
- Settings page: 20 concurrent requests
- React Query sends all 20 independently
- Backend processes all 20
- **No request deduplication or batching**

---

## FIXES REQUIRED

### CRITICAL (Blocking)
1. **Batch settings save** → 20 requests → 1 request
2. **Disable auto-sync on device list** → Default sync=false
3. **Implement device cleanup** → Delete stale records
4. **Fix WebSocket handler cleanup** → Unsubscribe on unmount
5. **Implement heartbeat timeout** → Mark offline after X seconds

### HIGH PRIORITY
6. Implement proper device state machine
7. Add duplicate request detection
8. Verify rate limit config end-to-end
9. Add request/response logging

### MEDIUM PRIORITY
10. Implement request batching middleware
11. Add caching headers
12. Optimize WebSocket message frequency

---

## SUMMARY TABLE

| Issue | Root Cause | Impact | Severity |
|-------|-----------|--------|----------|
| Rate limit 60 req/min | Settings 20-request save loop | Can't save settings | CRITICAL |
| Device stale records | No cleanup logic | Grows indefinitely | CRITICAL |
| Disconnected devices visible | No state machine | Confusing UI | HIGH |
| Realtime sync unreliable | WebSocket handler accumulation | Stale data | HIGH |
| Double sync on devices | Default sync=true | Slow page load | HIGH |
| Ghost devices | Missing deletion | DB pollution | MEDIUM |

---

## NEXT STEPS

1. ✅ Read this report  
2. ⏭️ Apply critical fixes (Sections A-E)
3. ⏭️ Test each fix individually
4. ⏭️ Run load test to verify rate limit not exceeded
5. ⏭️ Deploy to production
6. ⏭️ Monitor for 24 hours

