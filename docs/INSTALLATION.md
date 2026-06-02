# Installation Guide

## Prerequisites

- **Docker** 24+ and **Docker Compose** v2+
- **Python** 3.12+
- **Node.js** 20+
- **Android Debug Bridge (ADB)** - for device connectivity
- **Git**

## Docker Installation (Recommended)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd project-root
```

### 2. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your production values
# IMPORTANT: Change JWT_SECRET_KEY to a random 64-char hex string
```

### 3. Start Services

```bash
docker compose up -d
```

### 4. Verify Installation

```bash
# Check all services are running
docker compose ps

# Check backend health
curl http://localhost:8000/

# Check API docs
open http://localhost:8000/docs
```

### 5. Create Admin User

```bash
# The backend auto-creates tables on startup.
# Use the API to register the first admin:
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "username": "admin",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!"
  }'
```

## Local Development Installation

### Backend Setup

```bash
cd backend

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Environment file
cp .env.example .env
```

### Database Setup

Ensure PostgreSQL is running locally or use Docker for the database only:

```bash
# Start only database containers
docker compose up -d postgres redis

# Run migrations
alembic upgrade head

# Seed default settings
python scripts/seed_settings.py
```

### Run Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Environment file
cp .env.local.example .env.local

# Run development server
npm run dev
```

## Verifying ADB Connectivity

```bash
# Check ADB is installed
adb --version

# List connected devices
adb devices -l

# Start ADB server (if needed)
adb start-server
```

## Accessing Services

| Service   | URL                      | Credentials                          |
|-----------|--------------------------|--------------------------------------|
| Frontend  | http://localhost:3000    | User-defined during registration     |
| API       | http://localhost:8000    | JWT-based authentication             |
| Swagger   | http://localhost:8000/docs | JWT Bearer token                   |
| ReDoc     | http://localhost:8000/redoc | -                                  |
| pgAdmin   | http://localhost:5050    | admin@callreception.com / admin_secret |

## Stopping Services

```bash
# Stop all containers
docker compose down

# Stop and remove volumes (destroys data)
docker compose down -v
```

## Troubleshooting

### ADB Connection Issues
- Ensure ADB is installed: `adb --version`
- Check USB debugging is enabled on Android devices
- Verify device is authorized: `adb devices`

### Database Connection Issues
- Check PostgreSQL logs: `docker compose logs postgres`
- Verify connection string in `.env`

### Frontend API Issues
- Ensure `NEXT_PUBLIC_API_URL` points to the correct backend URL
- Check CORS configuration in backend settings
