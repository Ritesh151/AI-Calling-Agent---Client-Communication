#!/bin/bash

# AI Calling Agent - System Verification Script
# This script verifies that all system components are properly configured

echo "🔍 AI Calling Agent - System Verification"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Function to check command exists
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $1 is NOT installed"
        ((FAILED++))
        return 1
    fi
}

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $1 is MISSING"
        ((FAILED++))
        return 1
    fi
}

# Function to check directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $1 is MISSING"
        ((FAILED++))
        return 1
    fi
}

# Function to check port is listening
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":$1 "; then
        echo -e "${GREEN}✓${NC} Port $1 is listening"
        ((PASSED++))
        return 0
    else
        echo -e "${YELLOW}⚠${NC} Port $1 is NOT listening"
        ((WARNINGS++))
        return 1
    fi
}

echo "1. Checking System Dependencies"
echo "--------------------------------"
check_command python3
check_command node
check_command npm
check_command adb
check_command psql || echo -e "${YELLOW}⚠${NC} PostgreSQL client not found (optional)"
check_command redis-cli || echo -e "${YELLOW}⚠${NC} Redis client not found (optional)"
echo ""

echo "2. Checking Project Structure"
echo "------------------------------"
check_dir "backend"
check_dir "frontend"
check_dir "backend/app"
check_dir "frontend/src"
echo ""

echo "3. Checking Configuration Files"
echo "--------------------------------"
check_file "backend/.env"
check_file "frontend/.env.local"
check_file "backend/requirements.txt"
check_file "frontend/package.json"
echo ""

echo "4. Checking Backend Setup"
echo "-------------------------"
check_dir "backend/venv" || check_dir "backend/.venv" || echo -e "${YELLOW}⚠${NC} Virtual environment not found"
check_file "backend/app/main.py"
check_file "backend/app/core/config.py"
check_file "backend/app/core/database.py"
echo ""

echo "5. Checking Frontend Setup"
echo "--------------------------"
check_dir "frontend/node_modules" || echo -e "${YELLOW}⚠${NC} node_modules not found - run 'npm install'"
check_dir "frontend/.next" || echo -e "${YELLOW}⚠${NC} .next not found - run 'npm run build' or 'npm run dev'"
check_file "frontend/src/app/layout.tsx"
check_file "frontend/src/app/dashboard/layout.tsx"
echo ""

echo "6. Checking Services (if running)"
echo "----------------------------------"
check_port 8000 || echo "   Backend not running - start with: cd backend && uvicorn app.main:app --reload"
check_port 3000 || echo "   Frontend not running - start with: cd frontend && npm run dev"
check_port 5432 || echo "   PostgreSQL not running - start with: sudo systemctl start postgresql"
check_port 6379 || echo "   Redis not running - start with: sudo systemctl start redis"
echo ""

echo "7. Checking ADB"
echo "---------------"
if command -v adb &> /dev/null; then
    ADB_VERSION=$(adb version 2>&1 | head -n 1)
    echo -e "${GREEN}✓${NC} ADB Version: $ADB_VERSION"
    ((PASSED++))
    
    # Check ADB server
    if adb devices &> /dev/null; then
        echo -e "${GREEN}✓${NC} ADB server is running"
        ((PASSED++))
        
        # Check connected devices
        DEVICE_COUNT=$(adb devices | grep -v "List" | grep "device$" | wc -l)
        if [ $DEVICE_COUNT -gt 0 ]; then
            echo -e "${GREEN}✓${NC} $DEVICE_COUNT device(s) connected"
            ((PASSED++))
            adb devices | grep "device$"
            
        else
            echo -e "${YELLOW}⚠${NC} No devices connected"
            ((WARNINGS++))
        fi

    else
        echo -e "${RED}✗${NC} ADB server not running - run: adb start-server"
        ((FAILED++))
    fi
else
    echo -e "${RED}✗${NC} ADB not installed"
    ((FAILED++))
fi
echo ""

echo "8. Checking Python Dependencies"
echo "--------------------------------"
if [ -f "backend/requirements.txt" ]; then
    cd backend
    if [ -d "venv" ]; then
        source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
    elif [ -d ".venv" ]; then
        source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null
    fi
    
    if python3 -c "import fastapi" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} FastAPI installed"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} FastAPI not installed - run: pip install -r requirements.txt"
        ((FAILED++))
    fi
    
    if python3 -c "import sqlalchemy" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} SQLAlchemy installed"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} SQLAlchemy not installed"
        ((FAILED++))
    fi
    
    cd ..
fi
echo ""

echo "9. Environment Variables"
echo "------------------------"
if [ -f "backend/.env" ]; then
    if grep -q "POSTGRES_HOST" backend/.env; then
        echo -e "${GREEN}✓${NC} POSTGRES_HOST configured"
        ((PASSED++))
    fi
    if grep -q "REDIS_HOST" backend/.env; then
        echo -e "${GREEN}✓${NC} REDIS_HOST configured"
        ((PASSED++))
    fi
    if grep -q "JWT_SECRET_KEY" backend/.env; then
        echo -e "${GREEN}✓${NC} JWT_SECRET_KEY configured"
        ((PASSED++))
    fi
fi

if [ -f "frontend/.env.local" ]; then
    if grep -q "NEXT_PUBLIC_API_URL" frontend/.env.local; then
        echo -e "${GREEN}✓${NC} NEXT_PUBLIC_API_URL configured"
        ((PASSED++))
    fi
    if grep -q "NEXT_PUBLIC_WS_URL" frontend/.env.local; then
        echo -e "${GREEN}✓${NC} NEXT_PUBLIC_WS_URL configured"
        ((PASSED++))
    fi
fi
echo ""

echo "=========================================="
echo "Summary"
echo "=========================================="
echo -e "${GREEN}Passed:${NC} $PASSED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "${RED}Failed:${NC} $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ System verification PASSED${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Start backend: cd backend && uvicorn app.main:app --reload"
    echo "2. Start frontend: cd frontend && npm run dev"
    echo "3. Open browser: http://localhost:3000"
    echo "4. Check diagnostics: http://localhost:3000/diagnostics"
    exit 0
else
    echo -e "${RED}✗ System verification FAILED${NC}"
    echo ""
    echo "Please fix the failed checks above before starting the system."
    exit 1
fi
