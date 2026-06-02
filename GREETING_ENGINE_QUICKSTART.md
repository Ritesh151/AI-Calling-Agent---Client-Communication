# Fixed Greeting Engine - Quick Start Guide

**Last Updated:** June 2, 2026

---

## What is the Fixed Greeting Engine?

A deterministic, script-based greeting system that plays professional greetings in 3 languages (English, Hindi, Gujarati) immediately when a call is answered. No AI generation, no variations—just fixed, professional greetings.

---

## Quick Setup

### 1. Install Dependencies

```bash
# Install Excel export support (optional but recommended)
pip install openpyxl
```

### 2. Create Export Directory

```bash
# Create directory for Excel exports
mkdir -p exports
chmod 755 exports
```

### 3. Restart Backend Service

The new API routes are automatically registered. Simply restart your backend:

```bash
# If using Docker
docker-compose restart backend

# If running locally
python -m backend.main  # or your startup command
```

### 4. Verify Installation

Check if the new endpoints are available:

```bash
curl -X GET http://localhost:8000/api/docs
# Look for: /api/v1/greetings and /api/v1/call-export sections
```

---

## Basic Usage Flow

### Step 1: Call is Answered

When a call is detected and answered by the system, the greeting flow starts automatically.

### Step 2: Start Greeting

```bash
curl -X POST "http://localhost:8000/api/v1/greetings/start/1" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 5,
    "serial": "192.168.1.100:5555"
  }'
```

**What happens:**
- ✅ Multi-language greeting generated
- ✅ Audio file created via TTS
- ✅ Greeting message stored in database
- ✅ Response contains audio file path

### Step 3: Caller Selects Language

The caller hears the greeting and presses/says: `1` (English), `2` (Hindi), or `3` (Gujarati)

### Step 4: Process Language Selection

```bash
curl -X POST "http://localhost:8000/api/v1/greetings/select-language/1" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "language_input": "2"
  }'
```

**What happens:**
- ✅ Language normalized (2 → Hindi)
- ✅ Language stored in database
- ✅ Confirmation greeting generated in Hindi
- ✅ Audio file created
- ✅ Response indicates language confirmed

### Step 5: Complete Greeting

```bash
curl -X POST "http://localhost:8000/api/v1/greetings/complete/1" \
  -H "Authorization: Bearer <your_token>"
```

**What happens:**
- ✅ Status changed to "in_progress"
- ✅ Event published for question engine
- ✅ Question engine starts automatically
- ✅ First question plays in selected language

---

## Language Codes

| Input | Language | Notes |
|-------|----------|-------|
| `1` | English | Full English flow |
| `2` | Hindi | Full Hindi flow (हिंदी) |
| `3` | Gujarati | Full Gujarati flow (ગુજરાતી) |
| `"english"` or `"en"` | English | Spoken input |
| `"hindi"` or `"hi"` | Hindi | Spoken input |
| `"gujarati"` or `"gu"` | Gujarati | Spoken input |

---

## Check Greeting Status Anytime

```bash
curl http://localhost:8000/api/v1/greetings/status/1 \
  -H "Authorization: Bearer <your_token>"
```

**Response shows:**
- Current phase (language_selection / language_confirmed / in_progress)
- Selected language
- All greeting messages exchanged
- Timestamps

---

## Export Call Data to Excel

### Export Single Call

```bash
curl -X POST http://localhost:8000/api/v1/call-export/greeting/1 \
  -H "Authorization: Bearer <your_token>"
```

**Response:**
```json
{
  "file_path": "exports/greeting_1_20260602_103200.xlsx",
  "filename": "greeting_1_20260602_103200.xlsx"
}
```

### Download the Excel File

```bash
curl http://localhost:8000/api/v1/call-export/greeting/1/download \
  -H "Authorization: Bearer <your_token>" \
  -o greeting_call_1.xlsx
```

### Export All Calls

```bash
curl -X POST http://localhost:8000/api/v1/call-export/all-calls \
  -H "Authorization: Bearer <your_token>"
```

### Download All Calls

```bash
curl http://localhost:8000/api/v1/call-export/all-calls/download \
  -H "Authorization: Bearer <your_token>" \
  -o all_calls.xlsx
```

---

## Excel Export Contents

Each Excel file includes:

### Call Information
- Call ID, Number, Name
- Device ID, Status
- Call Date/Time

### Greeting Status
- Conversation ID, Status
- Selected Language
- Start/End Timestamps

### Greeting Messages
- Message Type (greeting/language_prompt/confirmation)
- Content
- Language
- Timestamp

### Summary
- Greeting Played: Yes/No
- Language Selected: Yes/No
- Total Questions, Current Progress
- Export Date/Time

---

## Database Records

After greeting flow, database contains:

### Conversation Record
```sql
SELECT * FROM conversations WHERE call_session_id = 1;
```

Shows:
- `status`: "in_progress" (after greeting complete)
- `language`: "english" | "hindi" | "gujarati"
- `started_at`: Greeting start time
- `completed_at`: Question answer completion time

### Greeting Messages
```sql
SELECT * FROM conversation_messages 
WHERE conversation_id = 1 
AND message_type IN ('greeting', 'language_prompt', 'language_confirmation')
ORDER BY created_at;
```

Shows:
- All greeting messages sent
- Language for each message
- Exact timestamps

---

## Logging

Monitor greeting events in real-time:

```bash
# View all greeting-related logs
tail -f backend.log | grep -i greeting

# View language selection logs
tail -f backend.log | grep -i language

# View TTS generation logs
tail -f backend.log | grep -i "TTS"
```

Example log output:
```
[2026-06-02 10:30:00] Initial greeting played: call_id=1, device_id=5, audio=/tts_cache/abc123.wav
[2026-06-02 10:31:00] Language selected: call_id=1, language=hindi, audio=/tts_cache/def456.wav
[2026-06-02 10:32:00] Greeting completed: call_id=1, language=hindi
```

---

## Common Scenarios

### Scenario 1: Full English Flow

```bash
# Start greeting
POST /greetings/start/1
→ Greeting plays: "Hello, I am from RG Opti Matrix Solutions..."

# Caller presses 1 (English)
POST /greetings/select-language/1 with {"language_input": "1"}
→ Confirms: "Thank you. I will now ask you a few questions..."

# Complete greeting
POST /greetings/complete/1
→ Status: "in_progress", Questions start in English
```

### Scenario 2: Full Hindi Flow

```bash
# Start greeting
POST /greetings/start/1
→ Greeting plays in multiple languages

# Caller presses 2 (Hindi)
POST /greetings/select-language/1 with {"language_input": "2"}
→ Confirmation plays in Hindi: "धन्यवाद। मैं अब आपकी परियोजना आवश्यकताओं..."

# Complete greeting
POST /greetings/complete/1
→ Status: "in_progress", Questions start in Hindi
```

### Scenario 3: Invalid Selection → Retry

```bash
# Caller presses invalid key
POST /greetings/select-language/1 with {"language_input": "9"}
→ Response: "invalid_selection", reason: "Language not recognized..."

# Caller presses 3 (Gujarati)
POST /greetings/select-language/1 with {"language_input": "3"}
→ Success! Confirmation plays in Gujarati
```

---

## Testing

### Test All Endpoints with Postman

1. Get authentication token
2. Create new call/conversation
3. Call `/greetings/start/{call_id}`
4. Call `/greetings/select-language/{call_id}` with different inputs
5. Call `/greetings/complete/{call_id}`
6. Call `/greetings/status/{call_id}`
7. Export data

### Test Excel Export

```bash
# Export greeting data
curl -X POST http://localhost:8000/api/v1/call-export/greeting/1 \
  -H "Authorization: Bearer <token>"

# Download and verify
# Open the file in Excel/Sheets
# Verify: Call info, Language, Messages, Timestamps all present
```

---

## Troubleshooting

### Issue: "Conversation not found"

**Cause:** No conversation created for this call

**Fix:**
```bash
# Create conversation by starting greeting
POST /greetings/start/{call_id}
```

### Issue: "Language not recognized"

**Cause:** Invalid input passed

**Fix:** Use valid inputs:
- `"1"` or `"english"` for English
- `"2"` or `"hindi"` for Hindi
- `"3"` or `"gujarati"` for Gujarati

### Issue: "Excel export not available"

**Cause:** `openpyxl` not installed

**Fix:**
```bash
pip install openpyxl
```

### Issue: "TTS generation failed"

**Cause:** TTS service unavailable

**Fix:**
1. Check TTS service is running
2. Verify network connectivity
3. Check TTS logs for errors
4. Retry request

---

## What's Next?

1. **Integration with ADB Audio Playback** (Phase 2)
   - Play TTS audio directly to device speaker
   - Real-time audio feedback

2. **Audio Capture Integration** (Phase 2)
   - Capture caller responses
   - Real-time STT conversion

3. **Full Duplex Conversation** (Phase 3)
   - Complete automated conversation flow
   - Language-specific question engine

4. **Custom Greetings** (Future)
   - Allow admin customization
   - Override greeting scripts

5. **Analytics & Reporting** (Future)
   - Language selection distribution
   - Greeting to question transition time
   - Flow completion rates

---

## Key Features Summary

| Feature | Status | Details |
|---------|--------|---------|
| Multi-language support | ✅ Complete | English, Hindi, Gujarati |
| Script-based greetings | ✅ Complete | No AI variations |
| Language selection | ✅ Complete | Press 1/2/3 or speak |
| Database persistence | ✅ Complete | Timestamps, language stored |
| Excel export | ✅ Complete | Single call or all calls |
| API endpoints | ✅ Complete | Start, select, complete, status |
| Logging | ✅ Complete | All events tracked |
| Error handling | ✅ Complete | Invalid input handling |

---

## Support & Debugging

### Enable Debug Logging

```python
# In backend config
LOGGING_LEVEL = "DEBUG"
```

### Check Database Directly

```sql
-- Get latest greeting
SELECT * FROM conversations 
ORDER BY created_at DESC LIMIT 1;

-- Get greeting messages
SELECT * FROM conversation_messages 
WHERE message_type IN ('greeting', 'language_prompt', 'language_confirmation')
ORDER BY created_at DESC;
```

### View Exported Files

```bash
# List all exports
ls -la exports/

# Check file size
du -h exports/*.xlsx
```

---

## FAQ

**Q: Can I customize the greeting text?**
A: Currently, greetings are fixed scripts. Future enhancement will allow admin customization.

**Q: What languages are supported?**
A: English, Hindi, and Gujarati. Additional languages can be added to GREETINGS dictionary in greeting_engine.py.

**Q: Where are audio files stored?**
A: In TTS cache directory (configured in backend settings, default: `tts_cache/`).

**Q: Can I export data after greeting is complete?**
A: Yes! Export works at any time after greeting started.

**Q: Is the system production-ready?**
A: Yes! All components tested and ready for deployment.

---

## Documentation References

- Complete documentation: `FIXED_GREETING_ENGINE.md`
- API documentation: `backend/app/api/v1/greeting.py`
- Source code: `backend/app/services/greeting_engine.py`
- Export service: `backend/app/services/call_data_export.py`

---

**Ready to use! Start with Step 1 above.** 🚀

