# Architecture Guide

## System Architecture

The AI Call Reception System follows a layered architecture pattern with clear separation of concerns.

```
┌──────────────────────────────────────────────────────────┐
│                   Presentation Layer                      │
│                    Next.js App Router                     │
│              Pages · Components · Layouts                 │
├──────────────────────────────────────────────────────────┤
│                   API Layer (Backend)                     │
│           FastAPI Routers · Middlewares · Auth            │
├──────────────────────────────────────────────────────────┤
│                   Service Layer                           │
│     Business Logic · Orchestration · Device Management   │
├──────────────────────────────────────────────────────────┤
│                   Repository Layer                        │
│           Data Access · Query Building · CRUD             │
├──────────────────────────────────────────────────────────┤
│                   Database Layer                          │
│          PostgreSQL · Redis · SQLAlchemy Models           │
└──────────────────────────────────────────────────────────┘
```

## Backend Architecture

### Layered Pattern

Each feature module follows a consistent layered architecture:

```
api/v1/{module}/
  router.py       → HTTP route definitions (thin)
service.py         → Business logic
repository.py      → Database access (thin)
```

### Request Flow

```
HTTP Request
    │
    ▼
FastAPI Router (validation via Pydantic)
    │
    ▼
Dependencies (auth, db session, permissions)
    │
    ▼
Service Layer (business logic, validation)
    │
    ▼
Repository Layer (database queries)
    │
    ▼
Database (PostgreSQL)
    │
    ▼
Response (formatted by Pydantic schema)
```

### Dependency Injection

Dependencies are injected via FastAPI's `Depends()`:

- **Database sessions** - `get_db()` provides SQLAlchemy sessions
- **Authentication** - `get_current_user_id()` extracts JWT user
- **Authorization** - `require_role()` validates user permissions

## Device Management Architecture

### Component Interaction

```
DeviceDiscoveryService
    │
    ├──► ADBManager (low-level ADB commands)
    │
    └──► DeviceRegistryService (DB registration)
              │
              └──► DeviceRepository (data access)

DeviceStatusService
    │
    ├──► ADBManager (heartbeat polling)
    │
    └──► DeviceRegistryService (status updates)
```

### ADB Abstraction

The `ADBManager` class abstracts all ADB commands:

- `connect()` - Start ADB server
- `disconnect()` - Kill ADB server
- `list_devices()` - List connected devices
- `get_device_info(serial)` - Get device properties
- `is_device_online(serial)` - Check device state
- `execute_command(serial, command)` - Execute shell command

### Heartbeat System

The `DeviceStatusService` runs a background loop:

1. Connect to ADB server
2. List all devices
3. For each device, get device info
4. Register or update in database
5. Sleep for configured interval
6. Repeat

## Frontend Architecture

### Component Tree

```
RootLayout
└── Providers (React Query, Theme)
    └── DashboardLayout
        ├── Sidebar (navigation, user info)
        ├── Header (breadcrumbs, theme toggle, user menu)
        └── Main Content (page components)
```

### State Management

**Server State** (React Query):
- Device list, call sessions, settings
- Automatic caching and invalidation
- Background refetching

**Client State** (Zustand):
- AuthStore - User session, authentication status
- DeviceStore - Device list cache
- SettingsStore - Settings key-value cache
- SystemStore - UI state (sidebar, theme)

### API Layer

```
React Component
    │
    ▼
Custom Hook (useAuth, useDevices)
    │
    ▼
React Query (caching, retry, invalidation)
    │
    ▼
Service (authService, devicesService)
    │
    ▼
Axios Client (base URL, interceptors)
    │
    ▼
Backend API
```

The Axios client includes:
- Automatic JWT attachment
- Token refresh on 401 responses
- Request queuing during refresh
- Error transformation

## Security Architecture

### Authentication Flow

```
1. User submits credentials
2. Backend validates and returns JWT tokens
3. Access token stored in httpOnly cookie + localStorage
4. Refresh token stored in httpOnly cookie
5. Every API request includes access token
6. On 401, client attempts refresh
7. Refresh fails → redirect to login
```

### JWT Token Structure

```json
{
  "sub": "user_id",
  "iat": 1234567890,
  "exp": 1234567890,
  "type": "access|refresh",
  "role": "user|admin",
  "email": "user@example.com"
}
```

## Database Design

### Entity Relationships

```
Users 1──* Devices 1──* CallSessions
Users 1──* SystemLogs (via service)
Settings (standalone key-value store)
```

### Migration Strategy

- Alembic for schema migrations
- Auto-generation of migration scripts
- Version-controlled migration history
- Both upgrade and downgrade paths
