# AI CONVERSATION PIPELINE - ROOT CAUSE AUDIT

**Date:** June 2, 2026  
**Status:** CRITICAL ISSUE IDENTIFIED  
**Priority:** P0 - Blocks Core Functionality

---

## EXECUTIVE SUMMARY

### The Problem
Call is answered successfully, but the AI cannot actually talk with the caller. No audio output from the system.

### Root Cause
**The conversation pipeline is 95% incomplete:**
- ✅ Call detected and answered
- ✅ Greeting message created in database
- ✅ Conversation object initialized
- ❌ **NO CODE TO PLAY AUDIO TO THE DEVICE**
- ❌ **NO STT (Speech-to-Text) implementation**
- ❌ **NO LLM (Language Model) integration**
- ❌ **NO TTS (Text-to-Speech) triggering**
- ❌ **NO AUDIO PLAYBACK to device speaker**

### The Gap
The system creates conversation messages but **never sends them to the device audio output**.

```
Current Flow:
Call Answered → Conversation Created → Message Added to Database → [NOTHING]

Required Flow:
Call Answered → Generate Greeting → TTS → Audio File → Send to Device Speaker → Caller Hears
                → Capture Audio → STT → Transcript → LLM → Response → TTS → Speaker → Loop
```

---

## DETAILED FAILURE ANALYSIS

### File: `backend/app/services/call_conversation/conversation_service.py`
**Line:** 47-63  
**Issue:** Creates greeting message but never plays it

```python
def ensure_for_call(self, call_session_id: int):
    # ...
    self._add_message(
        conversation,
        speaker="AI",
        message_type="language_prompt",
        content=LANGUAGE_SELECTION_GREETING,  # ❌ Text only, never converted to audio
        language=None,
    )
```

**What's Missing:**
1. Call to TTS to generate audio
2. Send audio to device speaker
3. Wait for user input
4. No callback to record user response

### File: `backend/app/workers/call_lifecycle_worker.py`
**Line:** 125-140  
**Issue:** Conversation started but no audio interaction flow

```python
await self._conversation.on_call_active(
    call_session_id=session_id,
    device_id=device.id,
    serial=serial,
    caller_number=event.caller_number,
    auto_answered=True,
)
# ❌ After this, nothing happens. No callback to play greeting.
```

**What's Missing:**
1. Async callback to handle audio playback
2. Event subscription for audio completion
3. Streaming audio handling
4. Input capture mechanism

---

## MISSING COMPONENTS

### 1. AUDIO PLAYBACK SERVICE
**Status:** NOT IMPLEMENTED  
**Required File:** `backend/app/services/audio_playback_service.py`

Should:
- Generate TTS audio from text
- Push audio to device via ADB
- Stream audio in real-time
- Monitor playback status
- Signal completion

### 2. AUDIO CAPTURE SERVICE
**Status:** PARTIAL (only recording, not streaming)  
**Required Enhancement:** Real-time audio streaming from device

Should:
- Capture audio from call while greeting is playing
- Stream to STT engine
- Provide transcription in real-time
- Signal speech detected

### 3. STT (SPEECH-TO-TEXT) SERVICE
**Status:** AVAILABLE (Whisper/Faster Whisper)  
**Issue:** Never called during conversation

**Location:** `backend/app/services/transcription/`  
**Missing:** Integration with real-time call audio

### 4. LLM RESPONSE GENERATION
**Status:** CONFIGURED but never invoked  
**Issue:** No logic to:
- Take transcribed text
- Generate response
- Select appropriate LLM
- Handle language

### 5. TTS TRIGGERING
**Status:** SERVICE EXISTS but never called  
**Location:** `backend/app/services/tts_engine/tts_service.py`  
**Issue:** `ensure_for_call()` creates message but doesn't call TTS

### 6. FULL DUPLEX CONVERSATION LOOP
**Status:** NOT IMPLEMENTED  
**Issue:** No mechanism for:
- Play greeting
- Wait for response
- Capture response
- Generate answer
- Play answer
- Repeat

---

## ARCHITECTURE BREAKDOWN

### Current (Broken)
```
Call Answered
    ↓
CallLifecycleWorker.on_call_answered()
    ↓
ConversationOrchestrator.on_call_active()
    ↓
ConversationService.ensure_for_call()
    ↓
Create message in database
    ↓
✅ Done (Nothing happens next!)
    ↓
Caller hears nothing
```

### Required (Full Implementation)
```
Call Answered (✅ Working)
    ↓
CallLifecycleWorker.on_call_answered()
    ↓
ConversationOrchestrator.on_call_active()
    ↓
ConversationService.ensure_for_call()
    ↓
Generate Greeting Message
    ↓
TTSService.generate_speech(greeting_text)
    ↓
AudioPlaybackService.play_to_device(audio_file)
    ↓
Device Speaker plays greeting (✅ Caller hears!)
    ↓
AudioCaptureService.stream_from_device()
    ↓
STTService.transcribe(audio_stream)
    ↓
Get Transcript (✅ Caller spoken response captured!)
    ↓
LLMService.generate_response(transcript)
    ↓
Get AI Response (✅ AI understands caller!)
    ↓
TTSService.generate_speech(response_text)
    ↓
AudioPlaybackService.play_to_device(audio_file)
    ↓
Device Speaker plays response (✅ Caller hears AI!)
    ↓
Loop continues...
```

---

## STEP-BY-STEP VERIFICATION RESULTS

### STEP 1: GREETING VALIDATION ❌ FAILED
**Expected:** System immediately speaks greeting after call answered  
**Actual:** Greeting message created in database, never played  
**Status:** No TTS triggered, no audio generation

### STEP 2: AUDIO CAPTURE VALIDATION ❌ FAILED
**Expected:** Caller speech being captured during/after greeting  
**Actual:** No audio capture mechanism during conversation  
**Status:** Recording service exists but not integrated

### STEP 3: STT VALIDATION ❌ FAILED
**Expected:** Audio converted to transcript  
**Actual:** No STT service called during conversation  
**Status:** Service available but unused

### STEP 4: LLM VALIDATION ❌ FAILED
**Expected:** Transcript sent to LLM for response generation  
**Actual:** No LLM integration in conversation flow  
**Status:** LLM configured but never invoked

### STEP 5: TTS VALIDATION ❌ FAILED
**Expected:** Response generated and converted to audio  
**Actual:** No TTS triggered for AI responses  
**Status:** TTS service exists but only for static messages

### STEP 6: FULL DUPLEX ❌ FAILED
**Expected:** Continuous conversation loop  
**Actual:** One-way system, no bidirectional audio  
**Status:** No event handling for conversation continuation

### STEP 7: DEBUGGING PANEL ❌ NOT IMPLEMENTED
**Missing:** `/conversation-debug` endpoint  
**Required:** Real-time conversation state visualization

### STEP 8: LANGUAGE SYSTEM ⚠️ PARTIAL
**Working:** Language selection persisted in database  
**Missing:** Language passed to TTS/LLM during playback

### STEP 9: REQUIREMENT GATHERING ⚠️ PARTIAL
**Working:** Questions stored after conversation  
**Missing:** Actual conversation to gather answers

---

## EXACT IMPLEMENTATION GAPS

| Component | Status | Location | Issue |
|-----------|--------|----------|-------|
| Greeting Playback | ❌ Missing | conversation_service.py | Text not converted to audio |
| Audio to Device | ❌ Missing | N/A | No ADB commands to play audio |
| Real-time Streaming | ❌ Missing | N/A | No streaming mechanism |
| STT Integration | ❌ Missing | conversation_service.py | Never called during conversation |
| LLM Integration | ❌ Missing | conversation_service.py | No response generation logic |
| Response Playback | ❌ Missing | N/A | Responses never spoken aloud |
| Event Loop | ❌ Missing | N/A | No async loop for conversation |
| Debug Endpoint | ❌ Missing | api/v1/conversations.py | No real-time status |
| Language Passing | ⚠️ Partial | conversation_service.py | Language selected but not used |

---

## CODE FLOW ANALYSIS

### What SHOULD happen after `ensure_for_call()`:

```python
async def ensure_for_call(self, call_session_id: int):
    # ... create conversation ...
    self._add_message(
        conversation,
        speaker="AI",
        message_type="language_prompt",
        content=LANGUAGE_SELECTION_GREETING,
        language=None,
    )
    
    # ❌ MISSING: Generate and play audio
    # audio_file = await TTSService.generate_speech(LANGUAGE_SELECTION_GREETING)
    # await AudioPlaybackService.play_to_device(device_id, audio_file)
    # await AudioCaptureService.listen_for_language_selection(call_session_id)
```

### What SHOULD happen after `select_language()`:

```python
async def select_language(self, call_session_id: int, language: str):
    # ... set language ...
    first_question = question_at(0)
    self._add_message(
        conversation,
        speaker="AI",
        message_type="question",
        content=first_question.text,
        language=selected,
    )
    
    # ❌ MISSING: Generate and play first question audio
    # audio_file = await TTSService.generate_speech(first_question.text, language=selected)
    # await AudioPlaybackService.play_to_device(device_id, audio_file)
    # await AudioCaptureService.listen_for_answer(call_session_id, first_question)
```

### What SHOULD happen after `record_answer()`:

```python
async def record_answer(self, call_session_id: int, answer: str):
    # ... record answer ...
    next_question = question_at(...)
    if next_question:
        self._add_message(
            conversation,
            speaker="AI",
            message_type="question",
            content=next_question.text,
            language=language,
        )
        
        # ❌ MISSING: Generate and play next question audio
        # audio_file = await TTSService.generate_speech(next_question.text, language=language)
        # await AudioPlaybackService.play_to_device(device_id, audio_file)
        # await AudioCaptureService.listen_for_answer(call_session_id, next_question)
```

---

## IMPLEMENTATION PRIORITY

### Phase 1: IMMEDIATE (Next 2 hours)
1. ✅ Create AudioPlaybackService
2. ✅ Implement device audio output via ADB
3. ✅ Trigger TTS in conversation flow
4. ✅ Test greeting playback

### Phase 2: CRITICAL (Next 4 hours)
1. ✅ Create AudioCaptureService for real-time streaming
2. ✅ Integrate STT with audio capture
3. ✅ Implement LLM response generation
4. ✅ Create conversation loop

### Phase 3: COMPLETE (Next 6 hours)
1. ✅ Full duplex audio handling
2. ✅ Language selection flow
3. ✅ Requirement gathering automation
4. ✅ Debugging panel

---

## TESTING CHECKLIST

After implementation, verify:

- [ ] Call answered → Greeting plays immediately (caller hears)
- [ ] Caller can speak during greeting
- [ ] Audio captured and transcribed
- [ ] STT shows transcript in logs
- [ ] LLM generates response
- [ ] Response converted to audio
- [ ] AI response plays to caller (caller hears AI)
- [ ] Next question plays after response
- [ ] Loop continues naturally
- [ ] All three languages work (English, Hindi, Gujarati)
- [ ] Conversation stored in database
- [ ] Requirements automatically extracted

---

## CONCLUSION

The AI conversation system is **95% infrastructure, 5% missing the voice interaction layer**.

**Root Cause:** No code to actually send audio TO the device speaker.

**Fix Complexity:** Medium (audio playback + event loop)

**Time Estimate:** 6 hours for full implementation

**Blocking:** Entire call experience

---

## NEXT STEPS

1. Implement AudioPlaybackService
2. Implement AudioCaptureService  
3. Integrate audio flow into ConversationService
4. Create debugging panel for visibility
5. Test end-to-end

**Target:** Full working call experience by end of today

