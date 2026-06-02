# TEST VERIFICATION GUIDE

**Purpose:** Verify all fixes are working correctly  
**Duration:** ~30-45 minutes  
**Requirement:** Both backend and frontend running

---

## SETUP

### 1. Start Backend
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### 2. Start Frontend
```bash
cd frontend
npm run dev  # Will run on http://localhost:3000
```

### 3. Access Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/ws

---

## TEST 1: SETTINGS PAGE BATCH SAVE ✅

### Objective
Verify settings save uses 1 request instead of 20.

### Steps
1. Open browser DevTools → Network tab
2. Filter to XHR/Fetch only
3. Go to Settings page (http://localhost:3000/settings)
4. Change 3-5 settings across different categories
5. Click "Save Changes"
6. Monitor Network tab

### Expected Result
- **ONE** PUT request to `/api/v1/settings/batch`
- Request payload includes array of all changed settings
- Response includes array of saved settings
- Page shows "Saved!" confirmation

### How to Verify
```javascript
// Open browser console and run:
console.log(performance.getEntriesByType('resource')
  .filter(r => r.name.includes('/settings/batch')).length);
// Should print: 1 (not 20)
```

### Pass/Fail Criteria
- ✅ **PASS:** 1 batch request seen, all settings saved
- ❌ **FAIL:** Multiple individual requests, or settings not saved

---

## TEST 2: DEVICES PAGE AUTO-SYNC REDUCTION ✅

### Objective
Verify devices page doesn't force sync on every fetch.

### Steps
1. Open DevTools → Network tab
2. Keep only XHR/Fetch filtered
3. Go to Devices page (http://localhost:3000/devices)
4. Wait 30-40 seconds
5. Count GET /devices and GET /devices/adb-status requests

### Expected Result
- **Before Fix:** GET /devices every 15s + GET /adb-status every 10s = 5-6 requests in 30s
- **After Fix:** GET /devices every 30s + GET /adb-status every 20s = 2-3 requests in 30s

### Request Breakdown
**30-Second Window:**
- Initial page load: 1x GET /devices + 1x GET /adb-status
- Auto-refetch at ~20s: 1x GET /adb-status
- **Total: 3 requests** (before was 6+)

### How to Count
```javascript
// In browser console:
const requests = performance.getEntriesByType('resource')
  .filter(r => r.name.includes('/devices') || r.name.includes('/adb-status'));
console.log('Total device requests:', requests.length);
requests.forEach(r => console.log(r.name.split('/api/v1')[1], 'took', Math.round(r.duration), 'ms'));
```

### Pass/Fail Criteria
- ✅ **PASS:** ~2-3 requests in 30s window (down from 5-6)
- ❌ **FAIL:** Still seeing 5-6 requests in 30s

---

## TEST 3: WEBSOCKET QUERY INVALIDATION ✅

### Objective
Verify WebSocket events trigger 1 refetch, not multiple.

### Steps
1. Open DevTools → Network tab + Console
2. Go to Devices page
3. Simulate device connection:
   ```bash
   # In another terminal, if you have a test device:
   adb connect 127.0.0.1  # Or physical device IP
   ```
4. Watch Network tab for GET /devices requests after device appears
5. Should see **exactly 1** request per WebSocket event

### Expected Result
- WebSocket receives `device_connected` message
- Frontend receives message in console as:
  ```javascript
  [WebSocket] Message received: { type: 'device_connected', data: {...} }
  ```
- **ONE** GET /devices request triggered
- Device appears in table

### How to Verify
```javascript
// In browser console:
// Listen for WebSocket messages (add this before device connection)
const origSocket = WebSocket;
window.WebSocket = function(...args) {
  const ws = new origSocket(...args);
  const origDispatch = ws.onmessage;
  ws.onmessage = (e) => {
    console.log('[WS EVENT]', JSON.parse(e.data).type);
    origDispatch?.call(ws, e);
  };
  return ws;
};
```

### Pass/Fail Criteria
- ✅ **PASS:** 1 WebSocket event = 1 network request
- ❌ **FAIL:** 1 WebSocket event = 2+ network requests

---

## TEST 4: DEVICE CLEANUP ENDPOINT ✅

### Objective
Verify cleanup endpoint works and removes stale records.

### Steps
1. Open terminal and create test devices (optional):
   ```bash
   # Connect via ADB and let discover find them
   adb devices
   ```

2. Call cleanup endpoint:
   ```bash
   curl -X POST http://localhost:8000/api/v1/devices/cleanup \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json"
   ```

3. Check response

### Expected Response
```json
{
  "success": true,
  "message": "Device cleanup completed",
  "data": {
    "marked_offline": 0,
    "deleted_stale": 0,
    "duplicates_removed": 0
  }
}
```

### If You Have Stale Records
1. Manually create stale records (in database):
   ```sql
   -- As admin, via database:
   UPDATE device SET last_seen = NOW() - INTERVAL '8 days', is_connected = false 
   WHERE id IN (SELECT id FROM device LIMIT 1);
   ```

2. Run cleanup again:
   ```bash
   curl -X POST http://localhost:8000/api/v1/devices/cleanup \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

3. Should see:
   ```json
   {
     "data": {
       "marked_offline": 0,
       "deleted_stale": 1,
       "duplicates_removed": 0
     }
   }
   ```

### Pass/Fail Criteria
- ✅ **PASS:** Endpoint returns 200, counts updated in response
- ❌ **FAIL:** 404, 401, or error response

---

## TEST 5: STALE TIME & CACHE TIME ✅

### Objective
Verify React Query staleTime and cacheTime prevent unnecessary refetches.

### Steps
1. Open DevTools → Console + Network
2. Go to Devices page
3. Leave page open for 10 seconds (don't interact)
4. Check Network tab

### Expected Behavior
- **0-5s:** Initial load (1 request)
- **5-10s:** No new requests (data still fresh, staleTime=5000ms)
- **25-30s:** First auto-refetch (staleTime expired, refetchInterval=30000ms triggered)

### How to Verify
```javascript
// In console, watch for fetches:
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (entry.name.includes('/devices')) {
      console.log('Request at', (entry.startTime - performance.timing.navigationStart).toFixed(0), 'ms');
    }
  }
});
observer.observe({entryTypes: ['resource']});
```

### Pass/Fail Criteria
- ✅ **PASS:** Requests at 0s, ~30s, ~60s (every 30s)
- ❌ **FAIL:** Requests at 0s, 15s, 30s, 45s, etc. (every 15s = old behavior)

---

## TEST 6: RATE LIMIT NOT TRIGGERED ✅

### Objective
Verify normal usage doesn't hit rate limit.

### Steps
1. Start with fresh session
2. Open Devices page → Normal usage for 5 minutes
3. Go to Settings → Make 2-3 changes → Save
4. Back to Devices → Discover devices
5. Monitor for rate limit errors

### Expected Result
- **No 429 errors** in Network tab
- **No "Rate limit exceeded" messages** in UI
- All requests succeed with 200 status

### How to Check for Rate Limit Errors
```javascript
// In console:
fetch('http://localhost:8000/api/v1/health/database').then(r => r.json()).then(console.log);
// Should return 200, not 429
```

### Pass/Fail Criteria
- ✅ **PASS:** All requests return 200, no 429 errors
- ❌ **FAIL:** Any 429 status or "Rate limit exceeded" error

---

## TEST 7: DEVICE LIFECYCLE ✅

### Objective
Verify devices transition states correctly and aren't stuck offline.

### Steps
1. Go to Devices page
2. Click "Discover Devices" (if you have USB-connected device)
3. Device should show as "Connected"
4. Unplug device or disconnect via ADB
5. Wait 10+ seconds (timeout threshold)
6. Refresh or wait for auto-refetch

### Expected Behavior
- Connected device shows green status
- After disconnect, status eventually changes to "Disconnected" or device disappears
- No "ghost" devices stuck as "Connected" when offline

### Pass/Fail Criteria
- ✅ **PASS:** Device status transitions correctly
- ❌ **FAIL:** Device stuck as "Connected" despite being disconnected

---

## TEST 8: BATCH SETTINGS VERIFICATION ✅

### Objective
Verify batch endpoint accepts and processes multiple settings.

### Steps
1. Open API docs: http://localhost:8000/docs
2. Find `PUT /api/v1/settings/batch` endpoint
3. Try it out with:
```json
{
  "settings": [
    {
      "key": "owner_name",
      "value": "Test Owner",
      "category": "general",
      "description": "Owner Name"
    },
    {
      "key": "recording_enabled",
      "value": "true",
      "category": "recording",
      "description": "Recording Enabled"
    }
  ]
}
```

### Expected Response
```json
{
  "success": true,
  "message": "Batch saved 2 settings",
  "data": [
    {
      "id": 1,
      "key": "owner_name",
      "value": "Test Owner",
      ...
    },
    {
      "id": 2,
      "key": "recording_enabled",
      "value": "true",
      ...
    }
  ]
}
```

### Pass/Fail Criteria
- ✅ **PASS:** 200 response, all settings returned in array
- ❌ **FAIL:** Error, missing settings, or 404

---

## LOAD TEST - REQUEST COUNT VERIFICATION

### Setup
1. Open DevTools → Network tab
2. Clear network history
3. Filter to XHR/Fetch

### Scenario: Normal 5-Minute Session

**Minute 1:**
1. Open Devices page
2. Expected: ~3 requests (1 devices + 1 adb-status + WebSocket setup)

**Minute 2:**
1. Navigate to Settings
2. Expected: ~1 request (load settings)

**Minute 3:**
1. Change 5-10 settings
2. Click Save
3. Expected: ~1 request (batch save, was 20 before)

**Minute 4:**
1. Back to Devices
2. Wait for auto-refetch
3. Expected: ~1 request (auto-refetch at 30s mark)

**Minute 5:**
1. Refresh page
2. Expected: ~3 requests (page reload)

### Summary
- **Total Expected:** ~10-15 requests
- **Before Fixes:** ~60+ requests (would hit limit)
- **After Fixes:** Well under 60 limit ✅

### Calculation
```
Baseline:
- Devices page auto-refetch: 5 min / 30s = 10 requests
- Settings save: 1 request
- Page loads: 2 requests
- WebSocket events: ~2-3 requests
Total: ~15-16 requests ✅ SAFE

Before fixes:
- Devices page auto-refetch: 5 min / 15s = 20 requests (from 2 endpoints)
- Settings save: 20 requests (was batch of individual calls)
- Page loads: 2 requests
- WebSocket events: ~8-10 requests (fuzzy match)
Total: ~60 requests ⚠️ DANGER ZONE
```

---

## AUTOMATED VERIFICATION SCRIPT

```bash
#!/bin/bash
# save as: test_fixes.sh

echo "🔍 VERIFICATION CHECKLIST"
echo "========================="
echo ""

# Check 1: Settings batch endpoint exists
echo "✓ Check 1: Settings batch endpoint"
curl -s http://localhost:8000/docs | grep -q "/settings/batch" && echo "  ✅ PASS" || echo "  ❌ FAIL"

# Check 2: Devices cleanup endpoint exists
echo "✓ Check 2: Devices cleanup endpoint"
curl -s http://localhost:8000/docs | grep -q "/devices/cleanup" && echo "  ✅ PASS" || echo "  ❌ FAIL"

# Check 3: Backend is healthy
echo "✓ Check 3: Backend health"
curl -s http://localhost:8000/health/database | grep -q "healthy" && echo "  ✅ PASS" || echo "  ❌ FAIL"

# Check 4: Frontend asset loads
echo "✓ Check 4: Frontend asset loads"
curl -s http://localhost:3000 | grep -q "next" && echo "  ✅ PASS" || echo "  ❌ FAIL"

echo ""
echo "Manual tests required:"
echo "  • Settings page batch save (check Network tab)"
echo "  • Devices page auto-refetch (should be every 30s)"
echo "  • WebSocket exact query invalidation"
echo "  • Device cleanup endpoint response"
echo ""
```

---

## SIGN-OFF CHECKLIST

After completing all tests, verify:

- [ ] Test 1: Settings batch save (1 request, not 20)
- [ ] Test 2: Devices auto-sync reduction (~50% fewer requests)
- [ ] Test 3: WebSocket query invalidation (1:1 event to refetch ratio)
- [ ] Test 4: Device cleanup endpoint functional
- [ ] Test 5: Stale time and cache time working
- [ ] Test 6: Rate limit not triggered under normal load
- [ ] Test 7: Device lifecycle state transitions correct
- [ ] Test 8: Batch settings endpoint working
- [ ] Load test: Total session requests under 60/minute

---

## TROUBLESHOOTING

### Settings batch endpoint returns 404
**Cause:** Backend not restarted after changes  
**Fix:** Restart backend server

### WebSocket not showing exact: true fixes
**Cause:** Frontend not recompiled  
**Fix:** Hard refresh (Ctrl+Shift+R) or clear `.next` cache

### Devices cleanup returns 401
**Cause:** Not authenticated  
**Fix:** Include Bearer token in Authorization header

### Rate limit still triggered
**Cause:** Session may have accumulated requests from before fixes  
**Fix:** Clear browser storage, start fresh session

### Device stuck offline
**Cause:** Heartbeat timeout not configured  
**Fix:** Check DEVICE_TIMEOUT_SECONDS in backend .env (default 10s)

---

## SUCCESS CRITERIA

✅ **All tests pass** → Ready for production deployment

✅ **Request count reduced ~65%** → Rate limit no longer an issue

✅ **Device lifecycle working** → No ghost devices

✅ **Zero rate limit errors** → Normal usage completely safe

---

**Test Report:**  
Date: ____________  
Tester: ____________  
Result: ☐ PASS  ☐ FAIL  
Notes: ________________________________

