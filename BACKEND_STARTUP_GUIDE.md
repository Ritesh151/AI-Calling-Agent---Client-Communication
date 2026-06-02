# Backend Startup Guide

**Date:** June 2, 2026  
**Status:** ✅ Fixed and Ready to Run

---

## Quick Start

```bash
cd project-root/backend

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Will watch for changes in these directories: ['/path/to/backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXX] using WatchFilesProcess
```

---

## Error: FileResponse ImportError (NOW FIXED ✅)

### If you see this error:
```
ImportError: cannot import name 'FileResponse' from 'fastapi'
```

**Solution:** This has been fixed in `backend/app/api/v1/call_export.py`

The import was changed from:
```python
from fastapi import APIRouter, Depends, FileResponse  # ❌ Wrong
```

To:
```python
from fastapi import APIRouter, Depends
from starlette.responses import FileResponse  # ✅ Correct
```

**Status:** ✅ FIXED - This error should no longer occur

---

## Prerequisites

### 1. Python 3.8+
```bash
python --version
# Output: Python 3.x.x
```

### 2. Virtual Environment Active
```bash
cd project-root/backend

# If venv not activated:
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### 3. Dependencies Installed
```bash
pip install -r requirements.txt
# or
pip install fastapi uvicorn sqlalchemy pydantic python-jose openpyxl
```

---

## Startup Process

### Step 1: Navigate to Backend
```bash
cd project-root/backend
```

### Step 2: Activate Virtual Environment
```bash
source venv/bin/activate
# or
source /path/to/venv/bin/activate
```

### Step 3: Start Uvicorn
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Options:**
- `--reload` - Auto-restart on file changes (development only)
- `--host 0.0.0.0` - Listen on all network interfaces
- `--port 8000` - Use port 8000
- `--workers 4` - Use 4 worker processes (production)

### Step 4: Verify Running
```bash
# In another terminal:
curl http://localhost:8000/api/docs
# Should return Swagger UI documentation
```

---

## Expected Startup Sequence

```
INFO:     Will watch for changes in these directories: ['/path/to/backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFilesProcess
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete
```

At this point, the backend is ready to accept requests.

---

## Accessing the Backend

### API Documentation
```
http://localhost:8000/api/docs
```
Interactive Swagger UI documentation

### Alternative Docs
```
http://localhost:8000/api/redoc
```
ReDoc documentation

### Health Check
```bash
curl http://localhost:8000/api/health
# or use any API endpoint to verify it's running
```

---

## Stopping the Backend

Press `CTRL+C` in the terminal where uvicorn is running:

```
^C
INFO:     Shutdown complete
```

---

## Common Issues & Solutions

### Issue 1: Port Already in Use
```
OSError: [Errno 48] Address already in use
```

**Solution:** Use a different port
```bash
uvicorn app.main:app --port 8001
```

Or kill the existing process:
```bash
# Find process on port 8000
lsof -i :8000
# Kill it
kill -9 <PID>
```

### Issue 2: Module Not Found
```
ModuleNotFoundError: No module named 'app'
```

**Solution:** Make sure you're in the correct directory:
```bash
cd project-root/backend
# Not: cd project-root
```

### Issue 3: Virtual Environment Not Activated
```
ImportError: cannot import name 'fastapi'
```

**Solution:** Activate virtual environment:
```bash
source venv/bin/activate
```

### Issue 4: Database Connection Error
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError)
```

**Solution:** Check database is running and credentials are correct
```bash
# Verify database connection in .env or config
cat backend/.env | grep DATABASE
```

---

## Configuration

### Environment Variables
Create or update `backend/.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/calling_agent

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# TTS
TTS_DEFAULT_PROVIDER=edge
TTS_CACHE_DIR=tts_cache
TTS_CACHE_ENABLED=true

# Logging
LOG_LEVEL=INFO

# Server
WORKERS=1
```

### Load Environment
```python
# This is done automatically by app.main
from app.core.config import settings
```

---

## Debugging

### Enable Debug Logging
```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Start uvicorn
uvicorn app.main:app --reload
```

### View Logs
```bash
# Logs go to stdout by default
# Pipe to file for analysis:
uvicorn app.main:app --reload > backend.log 2>&1
```

### Test Specific Endpoint
```bash
curl -X GET http://localhost:8000/api/v1/greetings/status/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

---

## Production Deployment

### Note on --reload
The `--reload` flag is ONLY for development. For production:

```bash
# Production: No reload, use workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or use Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 -k uvicorn.workers.UvicornWorker app.main:app
```

### SSL/HTTPS (Production)
```bash
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 443 \
  --ssl-keyfile=/path/to/key.pem \
  --ssl-certfile=/path/to/cert.pem
```

---

## Health Checks

### Quick Health Check
```bash
curl http://localhost:8000/api/v1/system/health
```

### Database Connection
```bash
curl http://localhost:8000/api/v1/system/database
```

### Full Status
```bash
curl http://localhost:8000/api/docs
# If this works, backend is running
```

---

## Performance Tips

### For Development
```bash
# Use reload with single worker
uvicorn app.main:app --reload
```

### For Testing
```bash
# No reload, but still single process
uvicorn app.main:app
```

### For Production
```bash
# Multiple workers for concurrency
uvicorn app.main:app --workers 4

# Or use Gunicorn + Uvicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

---

## Monitoring

### Watch Logs in Real-time
```bash
# Start in one terminal
uvicorn app.main:app --reload > server.log 2>&1

# In another terminal, watch:
tail -f server.log
```

### Monitor Specific Events
```bash
# Filter for greeting events
tail -f server.log | grep greeting

# Filter for errors
tail -f server.log | grep ERROR
```

---

## Troubleshooting Checklist

- [ ] Virtual environment activated (`which python` shows venv path)
- [ ] In correct directory (`pwd` shows `.../project-root/backend`)
- [ ] Dependencies installed (`pip list | grep fastapi`)
- [ ] Database configured (`.env` has DATABASE_URL)
- [ ] Database running (test connection)
- [ ] Port 8000 not in use (`lsof -i :8000`)
- [ ] All new files present:
  - [ ] `app/services/greeting_engine.py`
  - [ ] `app/api/v1/greeting.py`
  - [ ] `app/services/call_data_export.py`
  - [ ] `app/api/v1/call_export.py`

---

## Support

### Check These Files
- `ERROR_FIX_SUMMARY.md` - Details on the FileResponse fix
- `README_GREETING_ENGINE.md` - New greeting feature docs
- `FIXED_GREETING_ENGINE.md` - Complete technical docs

### For Help
1. Check error message carefully
2. Search for error in documentation
3. Check logs for details
4. Verify prerequisites
5. Try alternative port/host

---

## Summary

✅ Backend is ready to start with:
```bash
cd project-root/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ FileResponse import error has been fixed

✅ All new greeting engine files are in place

✅ Access API at: `http://localhost:8000/api/docs`

**Status:** Ready to run! 🚀

