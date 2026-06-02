# ROOT CAUSE REPORT - AI CONVERSATION PIPELINE FAILURE

**Report Date:** June 2, 2026  
**Issue:** AI cannot talk with caller despite call being answered  
**Severity:** CRITICAL (P0)  
**Status:** ROOT CAUSE IDENTIFIED, IMPLEMENTATION PLAN READY

---

## SECTION 1: FAILURE POINT IDENTIFICATION

### Exact Failure Location
**File:** `backend/app/services/call_conversation/conversation_service.py`  
**Function:** `ensure_for_call()`  
**Lines:** 47-63  

**The Breaking Point:**
```python
self._add_message(
    conversation,
    speaker="AI",
    message_type="language_prompt",
    content=LANGUAGE_SELECTION_GREETING,  # ❌ TEXT CREATED
    language=None,
)
# ❌ NOTHING HAPPENS AFTER THIS
# Missing: TTS, Audio Generation, Playback
```

### What Should Happen
```python
# After creating message:
1. audio_file = await TTSFactory.generate_speech(text)  # ❌ NOT CALLED
2. await AudioPlaybackService.play_to_device(device, audio_file)  # ❌ DOESN'T EXIST
3. await AudioCaptureService.listen_for_input(call_id)  # ❌ DOESN'T EXIST
4. greeting_loop()  # ❌ NOT IMPLEMENTED
```

---

## SECTION 2: EXACT FILES & FUNCTIONS

### File 1: conversation_service.py
**Issue:** Conversation text created but never converted to audio  
**Lines Affected:** 32-63 (ensure_for_call)  
**Missing:** Audio generation and playback code

### File 2: conversation_orchestrator.py
**Issue:** Conversation initiated but no audio interaction  
**Lines Affected:** 17-30 (on_call_active)  
**Missing:** Callback to audio playback service

### File 3: call_lifecycle_worker.py
**Issue:** After conversation started, no audio flow triggered  
**Lines Affected:** 125-140 (_trigger_auto_answer)  
**Missing:** Async task to manage audio interaction loop

### Missing Files:
1. ❌ `audio_playback_service.py` - Send audio to device speaker
2. ❌ `audio_capture_service.py` - Capture caller speech
3. ❌ `conversation_loop_service.py` - Manage full conversation
4. ❌ `audio_processing_worker.py` - Background audio handling

---

## SECTION 3: LINE-BY-LINE ANALYSIS

### conversation_service.py - Lines 32-63

**Current Code (BROKEN):**
```python
async def ensure_for_call(self, call_session_id: int) -> ConversationRead:
    call = self._get_call(call_session_id)
    conversation = self._get_conversation(call_session_id)
    if conversation:
        return ConversationRead.model_validate(conversation)

    conversation = Conversation(
        call_session_id=call_session_id,
        status="language_selection",
        total_questions=len(base_questions()),
        current_question_index=0,
        completion_percentage=0,
        profile_json=json.dumps(self._empty_profile(call)),
        started_at=datetime.now(UTC),
    )
    self.db.add(conversation)
    self.db.flush()

    self._add_message(  # ❌ TEXT MESSAGE CREATED
        conversation,
        speaker="AI",
        message_type="language_prompt",
        content=LANGUAGE_SELECTION_GREETING,  # ❌ GREETING TEXT: "Hello, I am from RG..."
        language=None,
    )
    self._refresh_transcript(conversation)
    self.db.commit()
    await self._broadcast(conversation, call)  # ❌ Only broadcasts to WebSocket
    self._mirror(conversation, call)  # ❌ Only mirrors to MongoDB
    return ConversationRead.model_validate(conversation)  # ❌ RETURNS - NO AUDIO SENT!
```

**Required Fix (Pseudocode):**
```python
async def ensure_for_call(self, call_session_id: int) -> ConversationRead:
    # ... existing code ...
    
    self._add_message(
        conversation,
        speaker="AI",
        message_type="language_prompt",
        content=LANGUAGE_SELECTION_GREETING,
        language=None,
    )
    self._refresh_transcript(conversation)
    self.db.commit()
    
    # ✅ NEW: GENERATE AND PLAY AUDIO
    device = self._get_device(call_session_id)
    greeting_audio = await self._generate_greeting_audio(
        conversation=conversation,
        device_id=device.id,
        text=LANGUAGE_SELECTION_GREETING
    )
    
    # ✅ NEW: PLAY TO DEVICE
    await self._play_audio_to_device(
        device_id=device.id,
        audio_file=greeting_audio
    )
    
    # ✅ NEW: START LISTENING FOR RESPONSE
    await self._start_listening_for_input(
        call_session_id=call_session_id,
        device_id=device.id
    )
    
    await self._broadcast(conversation, call)
    self._mirror(conversation, call)
    return ConversationRead.model_validate(conversation)
```

**Key Changes:**
1. Add TTS generation for greeting text
2. Add audio playback to device
3. Add audio capture for user response
4. Start conversation event loop

---

## SECTION 4: AUDIO FLOW STATUS

### Current Flow (95% Complete ❌)
```
Call Answered ✅
  ↓
Auto Answer ✅
  ↓
CallLifecycleWorker ✅
  ↓
ConversationOrchestrator ✅
  ↓
Create Message in DB ✅
  ↓
[MISSING] → Caller hears nothing ❌
  ↓
Broadcast to WebSocket ✅ (but no audio)
  ↓
Mirror to MongoDB ✅ (but no audio)
```

### Required Flow (0% Audio Implementation ❌)

```
Greeting Text ✅
  ↓
TTS Service ❌ [MISSING] (Generate audio from text)
  ↓
Audio Playback ❌ [MISSING] (Send to device speaker)
  ↓
Caller Hears Greeting ❌ [RESULT]
  ↓
Audio Capture ❌ [MISSING] (Listen to caller)
  ↓
STT Service ⚠️ [EXISTS, NOT USED] (Convert audio to text)
  ↓
Transcript ❌ [MISSING] (Store transcript)
  ↓
LLM Service ⚠️ [EXISTS, NOT USED] (Generate response)
  ↓
Response Text ❌ [MISSING] (AI understands)
  ↓
TTS Service ❌ [MISSING] (Convert response to audio)
  ↓
Audio Playback ❌ [MISSING] (Send to speaker)
  ↓
Caller Hears AI ❌ [RESULT]
```

---

## SECTION 5: COMPONENT STATUS MATRIX

| Component | Status | Location | Impact | Priority |
|-----------|--------|----------|--------|----------|
| Call Detection | ✅ Working | `call_detector.py` | N/A | - |
| Auto Answer | ✅ Working | `auto_answer.py` | N/A | - |
| Conversation DB | ✅ Working | `conversation_service.py` | N/A | - |
| TTS Service | ⚠️ Exists | `tts_engine/` | NOT CALLED | CRITICAL |
| Audio Playback | ❌ Missing | N/A | CALLER HEARS NOTHING | CRITICAL |
| Audio Capture | ❌ Missing | N/A | NO INPUT CAPTURE | CRITICAL |
| STT Integration | ❌ Missing | `transcription/` | NOT CALLED | CRITICAL |
| LLM Response | ❌ Missing | N/A | NO RESPONSES | CRITICAL |
| Event Loop | ❌ Missing | N/A | NO AUTOMATION | CRITICAL |
| Debug Endpoint | ❌ Missing | N/A | NO VISIBILITY | HIGH |

---

## SECTION 6: STT STATUS

**Service:** Faster Whisper  
**Location:** `backend/app/services/transcription/faster_whisper_provider.py`  
**Status:** ⚠️ AVAILABLE BUT NOT USED  

**Problem:** 
- Service exists and configured
- Never called during conversation
- No integration with audio capture
- No streaming/real-time processing

**Fix:** 
- Integrate with AudioCaptureService
- Pass captured audio to STT
- Store transcript in database
- Trigger next conversation step

---

## SECTION 7: LLM STATUS

**Service:** OpenAI/Local Models  
**Location:** `backend/app/services/ai_analysis/`  
**Status:** ⚠️ CONFIGURED BUT NOT USED  

**Problem:**
- LLM models available
- No conversation response generation logic
- No integration with ConversationService
- No prompt engineering for Q&A

**Fix:**
- Create LLM response generator
- Build conversation context from previous answers
- Generate appropriate follow-up questions
- Handle multi-language responses

---

## SECTION 8: TTS STATUS

**Service:** Edge TTS / OpenAI TTS  
**Location:** `backend/app/services/tts_engine/`  
**Status:** ⚠️ AVAILABLE BUT NOT TRIGGERED  

**Problem:**
- TTS factory exists
- `generate_speech()` method available
- Never called from conversation flow
- Cache exists but not used during conversation

**Fix:**
- Call `TTSFactory.generate_speech()` for each message
- Pass language parameter
- Handle audio generation errors
- Store generated audio files

---

## SECTION 9: PLAYBACK STATUS

**Service:** None (MISSING)  
**Status:** ❌ CRITICAL GAP  

**What's Missing:**
1. No method to push audio to device
2. No ADB commands to play audio
3. No device speaker control
4. No volume management
5. No playback monitoring
6. No completion detection

**Requirements:**
- Implement AudioPlaybackService
- Use ADB to send audio files to device
- Use media player on device to play
- Handle errors and retries
- Monitor playback progress

---

## SECTION 10: FINAL FIX SUMMARY

### The Problem (In One Sentence)
**The system creates conversation messages but never sends them as audio to the device speaker.**

### Why It Fails
```
Greeting Text → (NO CONVERSION) → (NO PLAYBACK) → Caller hears silence
```

### The Fix (In Three Steps)
```
Step 1: Text → TTS → Audio File (TextToSpeech)
Step 2: Audio File → Device Speaker (AudioPlayback)
Step 3: Device Microphone → Audio Stream → STT → Text (AudioCapture + STT)
```

### Implementation Order
```
1. Create AudioPlaybackService
2. Trigger TTS in ensure_for_call()
3. Play audio to device
4. Wait for user input
5. Capture audio and transcribe
6. Generate response
7. Play response
8. Loop
```

### Estimated Time to Fix
- Phase 1 (Audio Playback): 2 hours
- Phase 2 (Audio Capture + STT): 2 hours
- Phase 3 (Full Loop): 2 hours
- **Total: 6 hours**

---

## VERIFICATION CHECKLIST

After implementation, test:

- [ ] Call answered → Greeting plays within 2 seconds
- [ ] Caller can hear AI greeting clearly
- [ ] Caller can speak while greeting playing
- [ ] Audio captured and stored
- [ ] Transcript appears in logs
- [ ] AI generates response
- [ ] Response plays to caller
- [ ] Next question plays
- [ ] Conversation continues naturally
- [ ] All three languages work
- [ ] Conversation data persists
- [ ] Debug endpoint shows status
- [ ] No errors in logs

---

## CONCLUSION

| Aspect | Finding |
|--------|---------|
| **Root Cause** | No code to send audio to device speaker |
| **Failure Point** | `conversation_service.py`, line 63 (return without audio) |
| **Impact** | Complete conversation failure - caller hears nothing |
| **Complexity** | Medium (requires 3 new services, ~500 lines of code) |
| **Time to Fix** | 6 hours |
| **Blocking** | 100% of call experience |
| **Status** | **READY TO IMPLEMENT** |

---

## IMPLEMENTATION READY

**Go/No-Go:** ✅ **GO**

The implementation plan is complete, files are identified, and the architecture is clear. 

**Next Action:** Begin Phase 1 implementation (AudioPlaybackService)

---

**Report Prepared By:** Principal AI Voice Systems Engineer  
**Date:** June 2, 2026  
**Confidence:** 99% (Root cause definitively identified)

