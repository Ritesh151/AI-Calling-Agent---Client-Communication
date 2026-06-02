# 🚀 QUICK START GUIDE - AI Calling Agent

**Last Updated:** June 1, 2026  
**Status:** System Ready for Testing

---

## ⚡ FASTEST PATH TO RUNNING SYSTEM

### 1. Verify System (30 seconds)
```bash
./verify_system.sh
```

This will check:
- ✅ All dependencies installed
- ✅ Configuration files present
- ✅ Services ready to start

---

### 2. Start Backend (1 minute)
```bash
cd backend

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Verify:** Open http://localhost:8000/docs - You should see API documentation

---

### 3. Start Frontend (1 minute)
```bash
cd frontend

# Start development server
npm run dev
```

**Expected Output:**
```
  ▲ Next.js 15.x.x
  - Local:        http://localhost:3000
  - Ready in 2.5s
```

**Verify:** Open http://localhost:3000 - You should see login page

---

### 4. First Login (30 seconds)

**Option A: Register New User**
1. Go to http://localhost:3000/auth/register
2. Fill in:
   - Email: `admin@example.com`
   - Username: `admin`
   - Password: `admin123`
   - Confirm Password: `admin123`
3. Click "Register"

**Option B: Use Existing User**
1. Go to http://localhost:3000/auth/login
2. Login with credentials from database

---

### 5. Check System Health (30 seconds)
1. After login, navigate to: http://localhost:3000/diagnostics
2. Verify all indicators:
   - ✅ **Database** - Should be GREEN
   - ✅ **Redis** - Should be GREEN (if running)
   - ⚠️ **ADB** - May be YELLOW/RED (install if needed)
   - ⚠️ **Devices** - Will show 0/0 (no devices yet)

---

### 6. Test Settings (1 minute)
1. Navigate to: http://localhost:3000/settings
2. Change any setting (e.g., "Owner Name")
3. Click "Save Changes"
4. Wait for "Saved!" confirmation
5. Refresh page
6. Verify setting persisted ✅

---

### 7. Connect Android Device (2 minutes)

**Prerequisites:**
- Android device with USB debugging enabled
- USB cable
- ADB installed

**Steps:**
```bash
# 1. Enable USB debugging on Android:
#    Settings → About Phone → Tap "Build Number" 7 times
#    Settings → Developer Options → Enable "USB Debugging"

# 2. Connect device via USB

# 3. Verify ADB sees device
adb devices

# Expected output:
# List of devices attached
# ABC123XYZ    device

# 4. In browser, go to: http://localhost:3000/devices

# 5. Click "Discover Devices"

# 6. Device should appear in list ✅
```

---

## 🎯 WHAT WORKS NOW

### ✅ Fully Functional
- Frontend → Backend API connection
- User authentication (login/register)
- Settings persistence
- WebSocket real-time updates
- Device listing
- System diagnostics
- Health checks

### ⚠️ Requires Testing
- Device discovery via ADB
- Call detection
- Auto-answer
- Recording
- Transcription
- Background workers

### ❌ Not Yet Implemented
- Call history page
- Call detail page
- User management UI
- Logs viewer
- Metrics dashboard

---

## 🔧 TROUBLESHOOTING

### Backend Won't Start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
cd backend
pip install -r requirements.txt
```

---

**Error:** `sqlalchemy.exc.OperationalError: could not connect to server`

**Solution:**
```bash
# Start PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql   # Mac
# Or use Docker:
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=callreception_secret postgres
```

---

### Frontend Won't Start

**Error:** `Error: Cannot find module 'next'`

**Solution:**
```bash
cd frontend
npm install
```

---

**Error:** `Error: EADDRINUSE: address already in use :::3000`

**Solution:**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9  # Linux/Mac
# OR
netstat -ano | findstr :3000   # Windows (then kill PID)
```

---

### ADB Not Working

**Error:** `adb: command not found`

**Solution:**
```bash
# Linux
sudo apt install android-tools-adb

# Mac
brew install android-platform-tools

# Windows
# Download from: https://developer.android.com/studio/releases/platform-tools
```

---

**Error:** `adb devices` shows `unauthorized`

**Solution:**
1. Check Android device screen
2. Tap "Allow" on USB debugging prompt
3. Check "Always allow from this computer"
4. Run `adb devices` again

---

### WebSocket Not Connecting

**Symptom:** No real-time updates, console shows connection errors

**Solution:**
1. Verify backend is running on port 8000
2. Check `.env.local` has: `NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws`
3. Restart frontend: `npm run dev`
4. Check browser console for errors

---

### Settings Not Saving

**Symptom:** "Saved!" appears but settings don't persist

**Solution:**
1. Check backend logs for errors
2. Verify database connection in diagnostics
3. Ensure user has admin role
4. Check network tab for API errors

---

## 📊 SYSTEM REQUIREMENTS

### Minimum
- **OS:** Linux, macOS, or Windows 10+
- **RAM:** 4 GB
- **Storage:** 2 GB free space
- **Python:** 3.12+
- **Node.js:** 20+
- **PostgreSQL:** 14+
- **Redis:** 6+ (optional but recommended)

### Recommended
- **RAM:** 8 GB
- **Storage:** 10 GB free space
- **CPU:** 4 cores
- **GPU:** For faster transcription (optional)

---

## 🎓 LEARNING PATH

### Day 1: Setup & Configuration
- [x] Install dependencies
- [x] Configure environment
- [x] Start services
- [x] Verify system health

### Day 2: Device Integration
- [ ] Install ADB
- [ ] Connect Android device
- [ ] Test device discovery
- [ ] Monitor device status

### Day 3: Call Testing
- [ ] Simulate incoming call
- [ ] Test call detection
- [ ] Test auto-answer
- [ ] Verify recording

### Day 4: Transcription & Analysis
- [ ] Test transcription
- [ ] Review transcripts
- [ ] Test AI analysis
- [ ] Check embeddings

### Day 5: Production Readiness
- [ ] Configure production settings
- [ ] Set up monitoring
- [ ] Test error handling
- [ ] Performance optimization

---

## 📚 USEFUL COMMANDS

### Backend
```bash
# Start backend
cd backend && uvicorn app.main:app --reload

# Run migrations
cd backend && alembic upgrade head

# Create migration
cd backend && alembic revision --autogenerate -m "description"

# Check logs
tail -f backend/logs/app.log

# Run tests
cd backend && pytest
```

### Frontend
```bash
# Start frontend
cd frontend && npm run dev

# Build for production
cd frontend && npm run build

# Start production server
cd frontend && npm start

# Run tests
cd frontend && npm test

# Type check
cd frontend && npm run typecheck

# Lint
cd frontend && npm run lint
```

### ADB
```bash
# List devices
adb devices

# Start ADB server
adb start-server

# Kill ADB server
adb kill-server

# Get device info
adb shell getprop ro.product.model
adb shell getprop ro.build.version.release

# Check battery
adb shell dumpsys battery

# Check call state
adb shell dumpsys telephony.registry | grep mCallState
```

### Database
```bash
# Connect to database
psql -U callreception -d callreception

# List tables
\dt

# Describe table
\d devices

# Query devices
SELECT * FROM devices;

# Query settings
SELECT * FROM settings;
```

### Redis
```bash
# Connect to Redis
redis-cli

# Check connection
PING

# List keys
KEYS *

# Get value
GET key_name

# Monitor commands
MONITOR
```

---

## 🔗 USEFUL URLS

### Local Development
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Diagnostics:** http://localhost:3000/diagnostics
- **Settings:** http://localhost:3000/settings
- **Devices:** http://localhost:3000/devices

### Health Checks
- **Database:** http://localhost:8000/health/database
- **Redis:** http://localhost:8000/health/redis
- **ADB:** http://localhost:8000/health/adb
- **Devices:** http://localhost:8000/health/devices

---

## 🎉 SUCCESS INDICATORS

You know the system is working when:

1. ✅ Diagnostics page shows all green
2. ✅ Settings save and persist
3. ✅ WebSocket connects (check console)
4. ✅ Devices appear after discovery
5. ✅ Device status updates in real-time
6. ✅ No errors in backend logs
7. ✅ No errors in browser console

---

## 🆘 GETTING HELP

### Check Logs
```bash
# Backend logs
tail -f backend/logs/app.log

# Frontend logs
# Check browser console (F12)

# ADB logs
adb logcat
```

### Common Issues
1. **Port already in use** → Kill process or use different port
2. **Database connection failed** → Start PostgreSQL
3. **Redis connection failed** → Start Redis (optional)
4. **ADB not found** → Install ADB
5. **Device not detected** → Enable USB debugging

### Documentation
- See `AUDIT_REPORT.md` for detailed system analysis
- See `REPAIR_SUMMARY.md` for what was fixed
- See `README.md` for project overview

---

## 🚀 READY TO GO!

Your system is now configured and ready for testing. Start with the diagnostics page to verify everything is working, then proceed to connect your first device.

**Happy Testing! 🎊**
