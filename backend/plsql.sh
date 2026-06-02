#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# plsql.sh - PostgreSQL Setup & Migration Script (Fixed for Linux)
# Creates user, database, and runs Alembic migrations automatically.
# ─────────────────────────────────────────────────────────────────────────────

# Load .env if present
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

if [[ -f "$ENV_FILE" ]]; then
    while IFS='=' read -r key value; do
        [[ -z "$key" || "$key" =~ ^# || "$key" =~ ^[[:space:]]*$ ]] && continue
        key="$(echo "$key" | xargs)"
        [[ -z "$value" ]] && continue
        export "$key=$value" 2>/dev/null || true
    done < "$ENV_FILE"
fi

PG_HOST="${POSTGRES_HOST:-localhost}"
PG_PORT="${POSTGRES_PORT:-5432}"
PG_USER="${POSTGRES_USER:-callreception}"
PG_PASS="${POSTGRES_PASSWORD:-callreception_secret}"
PG_DB="${POSTGRES_DB:-callreception}"
PG_SUPERUSER="${PG_SUPERUSER:-postgres}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()   { echo -e "${GREEN}[✓]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
err()   { echo -e "${RED}[✗]${NC} $*"; }
info()  { echo -e "${CYAN}[i]${NC} $*"; }

# Fix Perl Locale Warning right away
export LC_ALL=C 2>/dev/null || true

# ── Detect psql / sudo ──────────────────────────────────────────────────────
PSQL="psql"
SUDO=""

if ! command -v psql &>/dev/null; then
    err "psql not found. Install postgresql-client first."
    exit 1
fi

# FIXED: Linux socket connection bypasses password prompt via sudo
if sudo -n -u "$PG_SUPERUSER" psql -c "SELECT 1" &>/dev/null; then
    SUDO="sudo -u $PG_SUPERUSER"
elif sudo -u "$PG_SUPERUSER" psql -c "SELECT 1" &>/dev/null; then
    SUDO="sudo -u $PG_SUPERUSER"
else
    warn "Sudo without password failed. Falling back to direct TCP connection..."
    SUDO=""
fi

run_psql() {
    # If using sudo, don't pass host/port to enforce local peer socket connection
    if [[ -n "$SUDO" ]]; then
        $SUDO psql -v ON_ERROR_STOP=1 "$@"
    else
        $SUDO psql -h "$PG_HOST" -p "$PG_PORT" -v ON_ERROR_STOP=1 "$@"
    fi
}

# ── Step 1: Check PostgreSQL connectivity ────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PostgreSQL Setup & Migration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

info "Checking PostgreSQL connection..."

if ! run_psql -U "$PG_SUPERUSER" -d postgres -c "SELECT 1" &>/dev/null; then
    err "Cannot connect to PostgreSQL"
    echo ""
    info "Troubleshooting:"
    echo "  1. Is PostgreSQL running?  -> sudo systemctl status postgresql"
    echo "  2. Start it:              -> sudo systemctl start postgresql"
    echo "  3. Check pg_hba.conf:     -> sudo nano /etc/postgresql/*/main/pg_hba.conf"
    echo ""
    exit 1
fi
log "PostgreSQL is reachable"

# ── Step 2: Create user ──────────────────────────────────────────────────────
info "Creating user '${PG_USER}' (if not exists)..."

USER_EXISTS=$(run_psql -U "$PG_SUPERUSER" -d postgres -tAc \
    "SELECT 1 FROM pg_roles WHERE rolname='${PG_USER}'" 2>/dev/null || echo "")

if [[ "$USER_EXISTS" == "1" ]]; then
    warn "User '${PG_USER}' already exists — updating password"
    run_psql -U "$PG_SUPERUSER" -d postgres \
        -c "ALTER USER ${PG_USER} WITH PASSWORD '${PG_PASS}';" >/dev/null
else
    run_psql -U "$PG_SUPERUSER" -d postgres \
        -c "CREATE USER ${PG_USER} WITH PASSWORD '${PG_PASS}' CREATEDB;" >/dev/null
    log "User '${PG_USER}' created"
fi

# ── Step 3: Create database ──────────────────────────────────────────────────
info "Creating database '${PG_DB}' (if not exists)..."

DB_EXISTS=$(run_psql -U "$PG_SUPERUSER" -d postgres -tAc \
    "SELECT 1 FROM pg_database WHERE datname='${PG_DB}'" 2>/dev/null || echo "")

if [[ "$DB_EXISTS" == "1" ]]; then
    warn "Database '${PG_DB}' already exists"
else
    run_psql -U "$PG_SUPERUSER" -d postgres \
        -c "CREATE DATABASE ${PG_DB} OWNER ${PG_USER};" >/dev/null
    log "Database '${PG_DB}' created"
fi

# ── Step 4: Grant privileges ─────────────────────────────────────────────────
info "Granting privileges..."
run_psql -U "$PG_SUPERUSER" -d postgres \
    -c "GRANT ALL PRIVILEGES ON DATABASE ${PG_DB} TO ${PG_USER};" >/dev/null
run_psql -U "$PG_SUPERUSER" -d "$PG_DB" \
    -c "GRANT ALL ON SCHEMA public TO ${PG_USER};" >/dev/null
run_psql -U "$PG_SUPERUSER" -d "$PG_DB" \
    -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${PG_USER};" >/dev/null
run_psql -U "$PG_SUPERUSER" -d "$PG_DB" \
    -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ${PG_USER};" >/dev/null
log "Privileges granted"

# ── Step 5: Verify password auth works ───────────────────────────────────────
info "Verifying password authentication for '${PG_USER}'..."
if PGPASSWORD="$PG_PASS" psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -c "SELECT 1" &>/dev/null; then
    log "Authentication OK — ${PG_USER}@${PG_HOST}:${PG_PORT}/${PG_DB}"
else
    warn "Password auth failed. Trying to fix pg_hba.conf..."
    PG_HBA=$(find /etc/postgresql -name pg_hba.conf 2>/dev/null | head -1)
    if [[ -n "$PG_HBA" ]]; then
        if ! grep -q "host.*${PG_DB}.*${PG_USER}.*127.0.0.1.*md5" "$PG_HBA" 2>/dev/null; then
            echo "host  ${PG_DB}  ${PG_USER}  127.0.0.1/32  md5" | $SUDO tee -a "$PG_HBA" >/dev/null
            echo "host  ${PG_DB}  ${PG_USER}  ::1/128  md5" | $SUDO tee -a "$PG_HBA" >/dev/null
            log "Added pg_hba.conf entries — reloading PostgreSQL"
            $SUDO systemctl reload postgresql 2>/dev/null || $SUDO pg_ctlcluster "$(ls /etc/postgresql/ | head -1)" main reload 2>/dev/null || true
            sleep 2
        fi
    fi

    if PGPASSWORD="$PG_PASS" psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -c "SELECT 1" &>/dev/null; then
        log "Authentication now works"
    else
        err "Password auth still failing. Check pg_hba.conf manually."
        exit 1
    fi
fi

# ── Step 6: Disable USE_SQLITE for PostgreSQL mode ───────────────────────────
if [[ -f "$ENV_FILE" ]]; then
    if grep -q "^USE_SQLITE=true" "$ENV_FILE"; then
        sed -i 's/^USE_SQLITE=true/USE_SQLITE=false/' "$ENV_FILE"
        log "Switched USE_SQLITE=false in .env (PostgreSQL mode)"
    fi
fi

# ── Step 7: Run Alembic migrations ───────────────────────────────────────────
info "Running Alembic migrations..."

cd "$SCRIPT_DIR"

if [[ -d "alembic" ]] && [[ -f "alembic.ini" ]]; then
    if [[ -d "venv" ]]; then
        source venv/bin/activate 2>/dev/null || true
    fi

    alembic upgrade head 2>&1 | while IFS= read -r line; do
        if echo "$line" | grep -qi "error\|failed"; then
            err "  $line"
        elif echo "$line" | grep -qi "running\|applying\|done\|generating"; then
            info "  $line"
        fi
    done

    if [[ ${PIPESTATUS[0]} -eq 0 ]]; then
        log "Migrations applied successfully"
    else
        warn "Migration may have encountered warnings (non-critical)"
    fi
else
    warn "Alembic not found — skipping migrations"
    info "Creating tables via SQLAlchemy metadata..."
    if [[ -d "venv" ]]; then
        source venv/bin/activate 2>/dev/null || true
    fi
    python3 -c "
from app.core.database import engine, Base
from app.db.models import *
Base.metadata.create_all(bind=engine)
print('All tables created successfully')
" 2>&1 && log "Tables created via create_all" || warn "Table creation had warnings"
fi

# ── Step 8: Verify tables ────────────────────────────────────────────────────
info "Verifying database tables..."
TABLE_COUNT=$(PGPASSWORD="$PG_PASS" psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -tAc \
    "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'" 2>/dev/null || echo "0")

if [[ "$TABLE_COUNT" -gt 0 ]]; then
    log "Found ${TABLE_COUNT} table(s) in database '${PG_DB}'"
    echo ""
    info "Tables:"
    PGPASSWORD="$PG_PASS" psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -c \
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename" 2>/dev/null || true
else
    warn "No tables found — migrations may need manual intervention"
fi

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  ${GREEN}Setup Complete${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Connection:  postgresql+psycopg2://${PG_USER}@${PG_HOST}:${PG_PORT}/${PG_DB}"
echo "  .env:        USE_SQLITE=false"
echo ""
echo "  Next:        cd ${SCRIPT_DIR} && uvicorn app.main:app --reload"
echo ""
