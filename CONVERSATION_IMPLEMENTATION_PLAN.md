# AI CONVERSATION IMPLEMENTATION - COMPLETE PLAN

**Objective:** Enable full duplex voice conversation between AI and caller  
**Timeline:** 6 hours (Phases 1-3)  
**Complexity:** Medium

---

## PHASE 1: AUDIO PLAYBACK (2 hours)

### Goal
Enable the system to play audio messages to the device speaker.

### Files to Create

#### 1. `backend/app/services/audio_playback_service.py`
Handles sending audio to device speaker via ADB

**Key Methods:**
- `play_to_device(device_id, audio_file_path)` - Play audio file
- `stop_playback(device_id)` - Stop current playback
- `is_playing(device_id)` - Check if device is currently playing
- `set_volume(device_id, volume_level)` - Set speaker volume

**Implementation Details:**
- Use `adb shell` to send audio file to device
- Use `adb push` to upload audio file
- Use `adb shell am` to trigger media player
- Monitor playback progress
- Wait for completion before next step

#### 2. Modified `backend/app/services/call_conversation/conversation_service.py`

**Changes in `ensure_for_call()`:**
```python
async def ensure_for_call(self, call_session_id: int) -> ConversationRead:
    # ... existing code ...
    
    # ✅ NEW: Play greeting after creating message
    device = self._get_device(call_session_id)
    greeting_audio = await self._generate_and_play_greeting(device, conversation)
    
    return ConversationRead.model_validate(conversation)

async def _generate_and_play_greeting(self, device, conversation):
    from app.services.audio_playback_service import AudioPlaybackService
    from app.services.tts_engine import TTSFactory
    
    # Generate speech
    greeting_text = LANGUAGE_SELECTION_GREETING
    audio_file = await TTSFactory.generate_speech(greeting_text)
    
    # Play to device
    playback_service = AudioPlaybackService(adb_engine)
    result = await playback_service.play_to_device(device.id, audio_file)
    
    return result
```

### Phase 1 Completion Criteria
- ✅ Greeting audio file generated
- ✅ Audio file sent to device
- ✅ Device speaker plays greeting
- ✅ Caller can hear system greeting
- ✅ Playback waits for completion

---

## PHASE 2: AUDIO CAPTURE & STT (2 hours)

### Goal
Capture caller speech and convert to text.

### Files to Create

#### 1. `backend/app/services/audio_capture_service.py`
Real-time audio capture and processing

**Key Methods:**
- `start_listening(device_id, call_session_id)` - Start capturing audio
- `stop_listening(device_id)` - Stop audio capture
- `get_audio_stream(device_id)` - Get raw audio stream
- `wait_for_speech(device_id, timeout=10)` - Wait for caller to speak

**Implementation Details:**
- Use `adb shell` with audio capture command
- Stream audio to local file or buffer
- Detect voice activity (silence detection)
- Trigger STT when speech detected

#### 2. Modified `backend/app/services/call_conversation/conversation_service.py`

**Changes in `ensure_for_call()` - Add listener after playing greeting:**
```python
# After playing greeting:
from app.services.audio_capture_service import AudioCaptureService

capture_service = AudioCaptureService(adb_engine)
await capture_service.start_listening(device.id, call_session_id)
await capture_service.wait_for_speech(device.id)
```

#### 3. `backend/app/workers/audio_processing_worker.py`
Background worker to handle audio processing

**Responsibilities:**
- Listen for audio capture events
- Trigger STT processing
- Store transcripts
- Signal completion

### Phase 2 Completion Criteria
- ✅ Audio capture from device working
- ✅ Caller speech detected
- ✅ Speech converted to transcript
- ✅ Transcript stored in database
- ✅ Next step triggered automatically

---

## PHASE 3: LLM & FULL DUPLEX (2 hours)

### Goal
Complete end-to-end conversation with AI responses.

### Files to Create

#### 1. `backend/app/services/conversation_loop_service.py`
Manages full conversation flow

**Key Methods:**
- `run_conversation_loop(call_session_id)` - Main conversation loop
- `process_user_input(call_session_id, transcript)` - Handle user speech
- `generate_ai_response(transcript, conversation_context)` - Get AI response
- `play_response(device_id, response_text)` - Play AI response

**Implementation Details:**
```python
async def run_conversation_loop(self, call_session_id):
    while conversation_active:
        # 1. Play question
        question_text = get_current_question()
        audio = await TTS.generate_speech(question_text)
        await AudioPlayback.play_to_device(device_id, audio)
        
        # 2. Wait for answer
        transcript = await AudioCapture.wait_for_speech(device_id)
        
        # 3. Record answer
        await ConversationService.record_answer(call_session_id, transcript)
        
        # 4. Get next question
        next_question = get_next_question()
        if not next_question:
            # Conversation complete
            break
```

#### 2. Modified `backend/app/workers/call_lifecycle_worker.py`

**Changes in `_trigger_auto_answer()`:**
```python
if session_id and session_id not in self._conversation_started:
    self._conversation_started.add(session_id)
    
    # ✅ NEW: Start full conversation loop
    from app.services.conversation_loop_service import ConversationLoopService
    
    loop_service = ConversationLoopService(adb_engine, event_bus)
    asyncio.create_task(
        loop_service.run_conversation_loop(
            call_session_id=session_id,
            device_id=device_id,
            serial=serial,
        )
    )
```

#### 3. `/conversation-debug` Endpoint

**File:** `backend/app/api/v1/conversations.py`

```python
@router.get("/debug/{call_session_id}", response_model=SuccessResponse[dict])
def get_conversation_debug(
    call_session_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    conversation = ConversationService(db).get_by_call(call_session_id)
    
    return SuccessResponse(data={
        "call_id": call_session_id,
        "status": conversation.status,
        "greeting_status": "played" if conversation.messages else "pending",
        "audio_capture_status": "listening",  # Real-time from worker
        "stt_status": "idle",  # Real-time from worker
        "current_question": conversation.current_question_index,
        "total_questions": conversation.total_questions,
        "completion": conversation.completion_percentage,
        "language": conversation.language,
        "last_error": None,  # From error tracking
        "latency_ms": {
            "greeting_to_speak": 1500,  # Real-time metrics
            "audio_capture": 2000,
            "stt_processing": 3000,
        },
        "messages": [
            {
                "speaker": msg.speaker,
                "content": msg.content,
                "timestamp": msg.created_at,
            }
            for msg in conversation.messages
        ],
    })
```

### Phase 3 Completion Criteria
- ✅ Full conversation loop working
- ✅ AI asks question
- ✅ Caller answers
- ✅ AI understands answer
- ✅ Question moves to next
- ✅ All three languages work
- ✅ Debug endpoint shows real-time status
- ✅ Conversation stored completely
- ✅ Requirements extracted automatically

---

## IMPLEMENTATION CHECKLIST

### Phase 1: Audio Playback
- [ ] Create AudioPlaybackService
- [ ] Implement ADB audio playback commands
- [ ] Modify ensure_for_call() to call TTS + playback
- [ ] Test greeting plays to device
- [ ] Test volume control
- [ ] Handle playback errors

### Phase 2: Audio Capture & STT
- [ ] Create AudioCaptureService
- [ ] Implement ADB audio capture commands
- [ ] Integrate STT service
- [ ] Create audio processing worker
- [ ] Handle silence detection
- [ ] Store audio + transcript

### Phase 3: Full Duplex
- [ ] Create ConversationLoopService
- [ ] Implement full conversation loop
- [ ] Integrate LLM response generation
- [ ] Create /conversation-debug endpoint
- [ ] Test end-to-end conversation
- [ ] Verify all languages work
- [ ] Test requirement extraction

---

## TESTING PROCEDURE

### Test 1: Greeting Playback
```bash
1. Make call to device
2. System answers automatically
3. Verify greeting plays immediately
4. Caller hears: "Hello, I am from RG Opti Matrix Solutions..."
Expected: ✅ Audio plays through speaker
```

### Test 2: Audio Capture
```bash
1. After greeting plays
2. Caller speaks language choice: "English"
3. Verify audio captured
4. Check logs for transcription
Expected: ✅ Transcript shows "english" or similar
```

### Test 3: Full Conversation
```bash
1. Select language
2. System asks: "May I know your full name?"
3. Caller responds: "John Smith"
4. System asks next question
5. Conversation continues
Expected: ✅ Complete back-and-forth conversation
```

### Test 4: Languages
```bash
1. Select Hindi
2. System speaks in Hindi
3. Caller responds in Hindi
4. Questions asked in Hindi
Expected: ✅ Entire conversation in Hindi
```

### Test 5: Debug Panel
```bash
1. Open http://localhost:3000/conversation-debug/{call_id}
2. Monitor real-time status
3. See message transcripts
4. See latency metrics
Expected: ✅ All data updates live
```

---

## ERROR HANDLING

### Common Issues

**Issue:** No audio playback
- Check ADB connection
- Verify device speaker is on
- Check volume level
- Check audio file format

**Issue:** Caller not heard
- Check microphone settings
- Verify audio input source
- Check STT service health
- Check audio permissions

**Issue:** AI doesn't respond
- Check LLM service connection
- Verify context window
- Check error logs
- Monitor token usage

**Issue:** Audio cuts off**
- Check network stability
- Verify buffer sizes
- Monitor CPU usage
- Check memory leaks

---

## DEPLOYMENT

### Pre-Deployment
1. Test all phases locally
2. Verify audio quality
3. Check error handling
4. Load test conversation loop

### Deployment Steps
1. Deploy Phase 1 code
2. Test greeting playback
3. Deploy Phase 2 code
4. Test audio capture
5. Deploy Phase 3 code
6. Test full conversation
7. Monitor logs
8. Enable debug endpoint

### Rollback
If issues occur:
1. Revert latest changes
2. Fall back to previous working version
3. Check logs for root cause
4. Fix and re-deploy

---

## SUCCESS CRITERIA

### Day 1 (By end of today)
- ✅ Greeting plays when call answered
- ✅ Caller can hear AI speak
- ✅ Audio captured from caller

### Day 2
- ✅ Transcription working
- ✅ Full conversation loop working
- ✅ AI generates responses
- ✅ Caller hears AI responses

### Day 3
- ✅ All three languages working
- ✅ Requirements gathered automatically
- ✅ Conversation stored in database
- ✅ System production-ready

---

## ESTIMATED EFFORT

| Task | Time | Priority |
|------|------|----------|
| AudioPlaybackService | 60 min | CRITICAL |
| Greeting Playback Integration | 30 min | CRITICAL |
| AudioCaptureService | 60 min | CRITICAL |
| STT Integration | 30 min | CRITICAL |
| ConversationLoopService | 60 min | HIGH |
| Full Duplex Testing | 45 min | HIGH |
| Debug Endpoint | 30 min | MEDIUM |
| Language Verification | 30 min | HIGH |
| Requirement Extraction | 15 min | MEDIUM |
| Error Handling | 30 min | HIGH |
| Documentation | 15 min | LOW |

**Total: ~6 hours**

---

## RISK MITIGATION

**Risk:** Audio quality poor  
**Mitigation:** Implement audio processing pipeline

**Risk:** Conversation loop gets stuck  
**Mitigation:** Add timeout handlers, circuit breakers

**Risk:** STT quality low  
**Mitigation:** Implement noise filtering, retries

**Risk:** LLM response generation fails  
**Mitigation:** Fallback responses, error handling

**Risk:** Device audio permissions missing  
**Mitigation:** Pre-check on device, guide user to enable

---

## CONCLUSION

This implementation will transform the AI Calling Agent from a database-only system to a **fully functional voice conversation system**.

After completion:
- ✅ Calls answered automatically
- ✅ AI speaks to caller
- ✅ Caller can respond
- ✅ Full conversation happens
- ✅ Requirements captured automatically
- ✅ Conversation stored for analysis

**Status:** Ready to implement

