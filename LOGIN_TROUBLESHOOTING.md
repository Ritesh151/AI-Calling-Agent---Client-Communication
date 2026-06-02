# Login Troubleshooting Guide

**Date:** June 2, 2026

---

## Quick Checks

### 1. Is Backend Running?
```bash
curl http://localhost:8000/api/docs
```
Should show Swagger UI

### 2. Test Login Endpoint Directly
```bash
# Test with curl
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "rg_admin@gmail.com",
    "password": "rg_admin123"
  }'

# Expected response:
# {
#   "status": "success",
#   "data": {
#     "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#     "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
#   },
#   "message": "Login successful"
# }
```

---

## Known Admin Credentials

From database fixtures:
```
Email: rg_admin@gmail.com
Password: rg_admin123
```

---

## Common Login Issues & Fixes

### Issue 1: "Invalid email or password"
**Cause:** User doesn't exist or password wrong  
**Fix:** 
- Verify user exists in database
- Use correct credentials
- Check password case sensitivity

**Check DB:**
```bash
# In backend terminal
sqlite3 calling_agent.db "SELECT id, email, is_active FROM users LIMIT 10;"
```

### Issue 2: "Account is deactivated"
**Cause:** User is_active = false  
**Fix:** Activate user in database
```sql
UPDATE users SET is_active = true WHERE email = 'your_email@gmail.com';
```

### Issue 3: "Invalid refresh token"
**Cause:** Token expired or malformed  
**Fix:** Login again to get fresh tokens

### Issue 4: 401 Unauthorized on API calls
**Cause:** Token not sent or expired  
**Fix:** Include token in headers
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/devices
```

### Issue 5: CORS Error
**Cause:** Frontend and backend on different domains  
**Fix:** Check CORS is enabled in backend
```python
# In app/main.py - should have:
from app.middlewares.cors import setup_cors
setup_cors(app)
```

---

## Frontend Login Issues

### Issue: Login button doesn't work
1. Open browser Dev Tools (F12)
2. Go to Network tab
3. Try to login
4. Check what response you get
5. Look at Console for JavaScript errors

### Issue: Stuck on login page after login
1. Check if token is being stored in localStorage
2. Check Network tab - what's the login response?
3. Check if API returns 200 with token

---

## Reset Login (Complete)

### Step 1: Create new admin user
```bash
cd project-root/backend
source venv/bin/activate
python

# Then in Python:
from app.core.database import SessionLocal
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password

db = SessionLocal()
repo = UserRepository(db)

user = repo.create(
    email="test@gmail.com",
    username="testuser",
    password_hash=hash_password("password123"),
    role="admin",
    is_active=True
)

db.commit()
print(f"Created user: {user.email}")
```

### Step 2: Login with new credentials
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@gmail.com",
    "password": "password123"
  }'
```

---

## Test Login Flow

### Via Swagger UI (Easiest)
1. Go to http://localhost:8000/api/docs
2. Find `/auth/login` endpoint
3. Click "Try it out"
4. Enter credentials:
   ```json
   {
     "email": "rg_admin@gmail.com",
     "password": "rg_admin123"
   }
   ```
5. Click Execute
6. Should see response with tokens

### Via Terminal
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "rg_admin@gmail.com",
    "password": "rg_admin123"
  }' \
  -c cookies.txt

# Use token to call protected endpoint
curl -X GET http://localhost:8000/api/v1/devices \
  -b cookies.txt
```

---

## What to Report

When asking for help with login, provide:

1. **Exact error message** (screenshot or text)
2. **Where you're logging in** (frontend URL, API endpoint, or Swagger)
3. **Which credentials** (email and if password is correct)
4. **Backend status** (is it running? any errors in logs?)
5. **Browser console errors** (Dev Tools > Console tab)
6. **Network response** (Dev Tools > Network tab, check login request)

---

## Quick Fix Commands

### Reinstall auth dependencies
```bash
cd project-root/backend
source venv/bin/activate
pip install python-jose passlib python-multipart
```

### Check backend can import auth
```bash
cd project-root/backend
source venv/bin/activate
python -c "from app.services.auth_service import AuthService; print('✅ Auth service imported')"
```

### Restart backend
```bash
# Kill existing uvicorn
pkill -f uvicorn

# Start fresh
bash project-root/backend/START_BACKEND.sh
```

---

## Still Not Working?

1. Open http://localhost:8000/api/docs
2. Try login endpoint with admin credentials
3. Copy the exact error response
4. Report with this information:
   - Error message
   - Response status code
   - Backend logs (any errors?)
   - Database check (user exists?)

---

**Status:** Authentication system is working. Need more info to debug your specific issue.

