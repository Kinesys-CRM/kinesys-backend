# Kinesys Backend

Async FastAPI backend for the Kinesys CRM platform. Provides RESTful APIs for lead management, Google Calendar integration, real-time WebSocket communication, and AI-powered voice agent capabilities via LiveKit.

## Features

- **Lead Management** — Full CRUD with soft deletes, filtering, pagination, Kanban views, tags, custom fields, and automatic stage history tracking
- **Google OAuth 2.0** — Authentication with JWT access/refresh token rotation and HttpOnly cookies
- **Google Calendar** — Create, read, update, delete events with automatic credential refresh and CRM lead linking
- **Booking System** — Timezone-aware appointment scheduling with availability engine and idempotent creation
- **Real-time Calls** — WebSocket infrastructure for agent-to-frontend message broadcasting
- **AI Voice Agent** — LiveKit integration for dynamic agent dispatch and room management

## Tech Stack

- **FastAPI** + **SQLModel** + **PostgreSQL** (asyncpg)
- **Alembic** for migrations
- **python-jose** for JWT
- **google-auth-oauthlib** + **google-api-python-client** for OAuth and Calendar
- **LiveKit SDK** for voice agent rooms
- **Pydantic v2** for validation and settings

## Prerequisites

- Python 3.12+
- PostgreSQL 14+ (or NeonDB/Supabase for serverless)
- Google Cloud project with OAuth 2.0 credentials
- LiveKit server (optional, for voice agent features)

## Quick Start

```bash
# Clone and install
git clone https://github.com/your-org/kinesys-backend.git
cd kinesys-backend
uv venv && source .venv/bin/activate
uv pip install -e .

# Configure
cp .env.example .env
# Edit .env with your credentials

# Run migrations and start
cd backend
alembic upgrade head
uvicorn app.main:app --reload --app-dir .
```

The API will be available at `http://localhost:8000` with docs at `/docs`.

## Configuration

Create a `.env` file in the project root:

```env
PROJECT_NAME=Kinesys
MODE=development
SECRET_KEY=your-secret-key-min-32-characters

# Google OAuth 2.0
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback

# Database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=your-password
DATABASE_NAME=kinesys

# Or override with full URI:
# ASYNC_DATABASE_URI=postgresql+asyncpg://user:pass@host:port/db?ssl=require

# LiveKit (optional)
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
```

## Project Structure

```
kinesys-backend/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py                # Dependency injection
│   │   │   └── v1/
│   │   │       ├── api.py             # Router aggregation
│   │   │       └── routers/
│   │   │           ├── auth.py        # Google OAuth endpoints
│   │   │           ├── leads.py       # Lead CRUD + metadata
│   │   │           ├── bookings.py    # Appointment scheduling
│   │   │           ├── calendar.py    # Google Calendar integration
│   │   │           ├── calls.py       # WebSocket call streaming
│   │   │           └── ai_calling.py  # LiveKit agent dispatch
│   │   ├── models/                    # SQLModel ORM models
│   │   ├── schemas/                   # Pydantic request/response schemas
│   │   ├── crud/                      # Database operations
│   │   ├── controllers/               # Business logic (OAuth flow)
│   │   ├── services/                  # WebSocket connection manager
│   │   ├── core/                      # Config and JWT utilities
│   │   ├── db/                        # Database engine setup
│   │   └── main.py                    # FastAPI app initialization
│   ├── alembic/                       # Database migrations
│   └── tests/                         # Test suite
├── pyproject.toml
└── README.md
```

## API Endpoints

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/login` | Redirect to Google OAuth |
| GET | `/callback` | OAuth callback (redirect) |
| GET | `/callback/json` | OAuth callback (JSON) |
| POST | `/refresh` | Refresh access token |
| POST | `/logout` | Invalidate refresh token |
| GET | `/me` | Current user profile |
| GET | `/users` | List users |

### Leads (`/api/v1/leads`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List leads (paginated, filterable) |
| POST | `/` | Create lead |
| GET | `/by-stage` | Leads grouped by pipeline stage |
| GET | `/{id}` | Get single lead |
| PUT | `/{id}` | Update lead |
| DELETE | `/{id}` | Soft delete lead |
| GET | `/meta/all` | All metadata for dropdowns |
| GET/POST/DELETE | `/tags` | Tag management |

### Bookings (`/api/v1/bookings`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/availability` | Available slots (next 7 days) |
| POST | `/create` | Book appointment (idempotent) |

### Calendar (`/api/v1/calendar`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/events` | List/create events |
| GET/PUT/DELETE | `/events/{id}` | Single event operations |
| GET | `/status` | Calendar connection status |
| GET | `/lead/{id}/events` | Events linked to a lead |

### AI Calling (`/api/v1/ai-calling`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/dispatch` | Dispatch AI agent to room |
| POST | `/token` | Generate participant token |
| GET | `/rooms` | List active rooms |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `WS /ws/agent` | Agent connection (broadcasts to frontends) |
| `WS /ws/calls/{call_id}` | Frontend subscription to call updates |

## Authentication Flow

1. `GET /api/v1/auth/login` — redirects to Google consent screen
2. Google redirects back to `/callback` with auth code
3. Server exchanges code for tokens, creates/finds user, returns JWT
4. Client sends `Authorization: Bearer <token>` on subsequent requests
5. `POST /api/v1/auth/refresh` rotates tokens via HttpOnly cookie

| Token | Lifetime | Storage |
|-------|----------|---------|
| Access | 15 min | Client localStorage |
| Refresh | 7 days | HttpOnly cookie |

## Database

```bash
cd backend

# Apply migrations
alembic upgrade head

# Generate new migration
alembic revision --autogenerate -m "description"

# Rollback
alembic downgrade -1
```

## Testing

```bash
uv pip install -e ".[test]"
cd backend
pytest -v
```

Tests use an in-memory SQLite database.

## Deployment

```bash
# Docker
docker build -t kinesys-backend .
docker run -p 8000:8000 --env-file .env kinesys-backend

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Production Checklist

- Set `MODE=production`
- Use a strong `SECRET_KEY` (32+ characters)
- Configure PostgreSQL with SSL
- Set up HTTPS via reverse proxy
- Update `ALLOWED_ORIGINS` in `main.py`

## License

MIT
