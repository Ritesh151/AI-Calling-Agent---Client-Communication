#!/bin/bash

# Backend Startup Script
# This script safely starts the backend with proper environment setup

set -e

echo "🚀 Starting AI Calling Agent Backend..."
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "📝 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "📝 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"

# Check if required packages are installed
echo "📝 Checking dependencies..."
python -c "import fastapi, uvicorn, sqlalchemy, starlette" 2>/dev/null || {
    echo "📝 Installing dependencies..."
    pip install --upgrade pip setuptools wheel
    pip install fastapi uvicorn sqlalchemy pydantic python-jose openpyxl starlette
    echo "✅ Dependencies installed"
}

# Verify app can be imported
echo "📝 Verifying application imports..."
python -c "from app.main import app; print('✅ Application verified')" || {
    echo "❌ Application import failed!"
    exit 1
}

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ Backend is ready to start!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Starting Uvicorn server..."
echo "📡 Access at: http://0.0.0.0:8000"
echo "📚 Docs at:  http://0.0.0.0:8000/api/docs"
echo ""
echo "Press CTRL+C to stop the server"
echo "════════════════════════════════════════════════════════════"
echo ""

# Start uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
