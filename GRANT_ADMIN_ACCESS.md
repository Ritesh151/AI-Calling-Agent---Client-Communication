# Grant Admin Access Guide

**Purpose:** Grant admin role to ritesh.work.1510@gmail.com  
**Status:** Ready to execute

---

## Method 1: Using Python Script (Easiest) ✅

### Step 1: Register the User First
If the user doesn't exist, register them at:
```
http://localhost:3000/auth/register
```

Or create them via API:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ritesh.work.1510@gmail.com",
    "username": "ritesh_admin",
    "password": "SecurePassword123!",
    "password_confirm": "SecurePassword123!"
  }'
```

### Step 2: Run the Grant Admin Script

```bash
# Navigate to backend
cd backend

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Run the script
python grant_admin.py ritesh.work.1510@gmail.com
```

**Expected Output:**
```
📋 User: ritesh_admin (ritesh.work.1510@gmail.com)
   Current role: user
✅ Admin access granted to ritesh.work.1510@gmail.com
   New role: admin
```

---

## Method 2: Using SQL (Direct Database)

### Step 1: Connect to Database
```bash
psql -U callreception -d callreception -h localhost
```

### Step 2: Update User Role
```sql
-- Check user exists
SELECT id, email, username, role FROM users WHERE email = 'ritesh.work.1510@gmail.com';

-- Grant admin access
UPDATE users 
SET role = 'admin' 
WHERE email = 'ritesh.work.1510@gmail.com';

-- Verify change
SELECT id, email, username, role FROM users WHERE email = 'ritesh.work.1510@gmail.com';
```

**Expected Output:**
```
 id |              email              |    username    | role
----+---------------------------------+----------------+-------
  5 | ritesh.work.1510@gmail.com      | ritesh_admin   | admin
```

---

## Method 3: Using pgAdmin (GUI)

### Step 1: Open pgAdmin
```
http://localhost:5050
```

### Step 2: Login
- **Username:** postgres (default)
- **Password:** (check your postgres setup)

### Step 3: Navigate to Database
1. Servers → PostgreSQL → Databases → callreception → Schemas → public → Tables → users
2. Right-click "users" → View/Edit Data → All Rows

### Step 4: Edit User Row
1. Find row with email: `ritesh.work.1510@gmail.com`
2. Change `role` column from `user` to `admin`
3. Click "Save" button

---

## Method 4: Using Django/Flask Shell (If Available)

```bash
cd backend
python shell

# In Python shell:
from app.db.models.user import User
from app.core.database import SessionLocal

db = SessionLocal()
user = db.query(User).filter(User.email == 'ritesh.work.1510@gmail.com').first()
user.role = 'admin'
db.commit()
print(f"Admin access granted: {user.role}")
```

---

## Verification

After granting admin access, verify it worked:

### Option 1: Login and Check Role
1. Go to http://localhost:3000/auth/login
2. Login with:
   - Email: `ritesh.work.1510@gmail.com`
   - Password: (whatever was set)
3. Go to http://localhost:3000/settings
4. Settings should now be editable (no more role errors) ✅

### Option 2: Check API Response
```bash
# Login and get token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ritesh.work.1510@gmail.com",
    "password": "your_password"
  }'

# You'll get access_token in response
# Use it to call admin endpoint:
curl -X POST http://localhost:8000/api/v1/devices/cleanup \
  -H "Authorization: Bearer <access_token>"

# Should return 200 if user is admin
```

### Option 3: Database Query
```sql
SELECT email, role FROM users WHERE email = 'ritesh.work.1510@gmail.com';
-- Should show: role = 'admin'
```

---

## Troubleshooting

### User Not Found Error
**Problem:** Script says "User not found"  
**Solution:** The user must exist in the database first. Either:
1. Register via frontend: http://localhost:3000/auth/register
2. Create via API using curl command in Method 1, Step 1
3. Check the email is spelled correctly

### Database Connection Error
**Problem:** "Could not connect to database"  
**Solution:**
1. Verify PostgreSQL is running:
   ```bash
   sudo systemctl status postgresql  # Linux
   brew services list | grep postgres # Mac
   ```
2. Check DATABASE_URL in `.env`:
   ```bash
   cat backend/.env | grep DATABASE_URL
   ```
3. Verify credentials are correct

### Permission Denied Error
**Problem:** "Permission denied" when running Python script  
**Solution:**
```bash
# Make script executable
chmod +x backend/grant_admin.py

# Then run it
python backend/grant_admin.py ritesh.work.1510@gmail.com
```

---

## Quick Summary

| Method | Time | Difficulty | Notes |
|--------|------|-----------|-------|
| Python Script | 1 min | Easy | Recommended ✅ |
| SQL Query | 2 min | Medium | Direct but requires psql |
| pgAdmin GUI | 3 min | Easy | Visual but requires setup |
| Shell | 2 min | Medium | Only if shell available |

---

## Commands to Copy & Paste

### Register User (if needed)
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ritesh.work.1510@gmail.com",
    "username": "ritesh_admin",
    "password": "SecurePassword123!",
    "password_confirm": "SecurePassword123!"
  }'
```

### Grant Admin Access (Fastest)
```bash
cd backend
source venv/bin/activate
python grant_admin.py ritesh.work.1510@gmail.com
```

### Verify Admin Status
```bash
psql -U callreception -d callreception -c \
  "SELECT email, role FROM users WHERE email = 'ritesh.work.1510@gmail.com';"
```

---

## Next Steps

1. ✅ Choose a method from above
2. ✅ Execute the command
3. ✅ Verify using one of the verification methods
4. ✅ Login and test
5. ✅ Settings page should now work without errors

---

**Status:** Ready to execute  
**Time Required:** ~2 minutes  
**Difficulty:** Easy

