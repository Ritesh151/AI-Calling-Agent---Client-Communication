-- Grant Admin Access Script
-- This file contains SQL commands to grant admin access to a user

-- ===========================================================================
-- IMPORTANT: Execute these commands in order
-- ===========================================================================

-- 1. First, check if user exists
SELECT id, email, username, role, is_active 
FROM users 
WHERE email = 'ritesh.work.1510@gmail.com';

-- Expected output: Should show one row with the user details
-- If no results, the user needs to be registered first via the web interface


-- 2. Update user role to admin
UPDATE users 
SET role = 'admin'
WHERE email = 'ritesh.work.1510@gmail.com';

-- Expected output: UPDATE 1 (if user found and updated)


-- 3. Verify the change was successful
SELECT id, email, username, role, is_active 
FROM users 
WHERE email = 'ritesh.work.1510@gmail.com';

-- Expected output: Should show role = 'admin'


-- ===========================================================================
-- HOW TO USE THIS FILE
-- ===========================================================================

-- Option 1: Copy and paste each command into psql
-- $ psql -U callreception -d callreception
-- callreception=# PASTE COMMANDS ABOVE

-- Option 2: Use psql with file
-- $ psql -U callreception -d callreception -f grant_admin.sql

-- Option 3: Use psql from anywhere
-- $ psql -U callreception -d callreception -h localhost -f /path/to/grant_admin.sql

-- ===========================================================================
-- TROUBLESHOOTING
-- ===========================================================================

-- If you get "ERROR: role 'callreception' does not exist":
-- Replace 'callreception' with your PostgreSQL username

-- If you get "FATAL: database 'callreception' does not exist":
-- Create the database first:
-- $ createdb -U postgres callreception

-- If you get connection refused:
-- Make sure PostgreSQL is running:
-- $ sudo systemctl start postgresql  (Linux)
-- $ brew services start postgresql   (Mac)

-- ===========================================================================
