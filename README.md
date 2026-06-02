# AI Calling System - Developed by `Ritesh Gajjar`

A production-grade AI-powered call reception system that manages incoming calls on USB-connected Android devices, records messages, generates transcripts, and provides a web dashboard for management.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (Next.js 15)                   │
│              TypeScript · Tailwind · Shadcn UI             │
│              React Query · Zustand · Axios                │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/HTTPS
┌──────────────────────▼──────────────────────────────────┐
│                   Backend (FastAPI)                       │
│              Python 3.12 · SQLAlchemy 2.0 · Pydantic v2   │
│              JWT Auth · Rate Limiting · CORS              │
├──────────────────────┬───────────────────────────────────┤
│      API v1          │         Services                   │
│  ┌──────────────┐    │  ┌──────────────────────────┐      │
│  │  auth        │    │  │  AuthService             │      │
│  │  users       │    │  │  DeviceService           │      │
│  │  devices     │    │  │  ADBManager              │      │
│  │  calls       │    │  │  DeviceDiscoveryService  │      │
│  │  settings    │    │  │  DeviceRegistryService   │      │
│  │  logs        │    │  │  DeviceStatusService     │      │
│  │  system      │    │  │  CallSessionService      │      │
│  └──────────────┘    │  │  SettingService          │      │
│                      │  │  LogService              │      │
│                      │  └──────────────────────────┘      │
├──────────────────────┴───────────────────────────────────┤
│              Database (PostgreSQL)                        │
│              Cache (Redis)                                │
└──────────────────────────────────────────────────────────┘
```

## Tech Stack

### Frontend
- **Next.js 15+** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Shadcn UI** - Reusable component library
- **React Query** - Server state management
- **Zustand** - Client state management
- **Axios** - HTTP client with interceptors
- **React Hook Form** - Form management
- **Zod** - Schema validation

### Backend
- **Python 3.12+** - Modern Python
- **FastAPI** - High-performance async framework
- **SQLAlchemy 2.0** - ORM with async support
- **Alembic** - Database migrations
- **Pydantic v2** - Data validation
- **PostgreSQL** - Primary database
- **Redis** - Caching and rate limiting

### DevOps
- **Docker** & **Docker Compose** - Containerization
- **Ruff** / **Black** - Python linting and formatting
- **MyPy** - Static type checking
- **Pre-commit** - Git hooks
- **pytest** - Backend testing
- **Vitest** - Frontend testing

## Project Structure

```
project-root/
├── frontend/                 # Next.js application
│   ├── src/
│   │   ├── app/              # App Router pages
│   │   │   ├── auth/         # Login & Register
│   │   │   ├── dashboard/    # Dashboard widgets
│   │   │   ├── devices/      # Device management
│   │   │   ├── calls/        # Call sessions
│   │   │   ├── settings/     # System settings
│   │   │   └── profile/      # User profile
│   │   ├── components/       # Reusable components
│   │   │   ├── ui/           # Base UI components
│   │   │   ├── layout/       # Layout components
│   │   │   ├── devices/      # Device components
│   │   │   ├── calls/        # Call components
│   │   │   ├── settings/     # Settings components
│   │   │   └── dashboard/    # Dashboard components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── services/         # API client services
│   │   ├── stores/           # Zustand stores
│   │   ├── types/            # TypeScript types
│   │   └── lib/              # Utility functions
│   └── public/
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── api/v1/           # API routes
│   │   │   ├── auth/         # Authentication endpoints
│   │   │   ├── users/        # User management
│   │   │   ├── devices/      # Device management
│   │   │   ├── calls/        # Call sessions
│   │   │   ├── settings/     # System settings
│   │   │   ├── logs/         # System logs
│   │   │   └── system/       # System endpoints
│   │   ├── core/             # Core configuration
│   │   ├── db/models/        # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── repositories/     # Data access layer
│   │   ├── middlewares/      # FastAPI middlewares
│   │   └── utils/            # Utility functions
│   ├── tests/                # pytest tests
│   └── alembic/              # Database migrations
├── docker/                   # Docker configurations
├── docs/                     # Documentation
└── scripts/                  # Utility scripts
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.12+ (for local development)
- Node.js 20+ (for local development)
- Android Debug Bridge (ADB)

### Development with Docker

```bash
# Clone and enter project
git clone <repository-url>
cd project-root

# Start all services
docker compose up -d

# Services will be available at:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# pgAdmin: http://localhost:5050
```

### Local Development

#### Backend
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## API Documentation

Interactive API documentation is available at `/docs` (Swagger UI) and `/redoc` (ReDoc) when the backend is running.

### Authentication
All protected endpoints require a valid JWT access token in the `Authorization: Bearer <token>` header or as an httpOnly cookie.

## Database Schema

### Tables
- **users** - User accounts and authentication
- **devices** - Connected Android device registry
- **call_sessions** - Incoming call records
- **system_logs** - Application logs
- **settings** - System configuration key-value store

## Security

- JWT access + refresh token rotation
- bcrypt password hashing (12 rounds)
- httpOnly secure cookies
- CORS with allowed origin whitelist
- Rate limiting per client IP
- Input validation via Pydantic/Zod
- SQL injection protection via ORM
- XSS protection via output encoding
- Environment-based secrets management

## License

MIT
