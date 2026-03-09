# MyApp — Rails-style FastAPI framework

A **production-ready FastAPI boilerplate** that mirrors Ruby on Rails conventions: controllers with filters, ActiveRecord-style models with callbacks, centralized routing, services, background jobs, and a full CLI.

---

## Table of contents

- [Tech stack](#tech-stack)
- [Features](#features)
- [Project structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment configuration](#environment-configuration)
- [Database](#database)
- [Running the application](#running-the-application)
- [CLI reference](#cli-reference)
- [API reference](#api-reference)
- [Architecture](#architecture)
- [Testing](#testing)
- [Background jobs](#background-jobs)
- [Deployment](#deployment)

---

## Tech stack

| Layer        | Technology |
|-------------|------------|
| **Language** | Python 3.11+ |
| **Web**      | FastAPI (latest), Uvicorn |
| **ORM**      | SQLAlchemy 2.0 |
| **Migrations** | Alembic |
| **Validation** | Pydantic v2 |
| **Database** | PostgreSQL |
| **Cache / queue** | Redis |
| **Background jobs** | Celery |
| **Auth**     | JWT (python-jose), Passlib + bcrypt |
| **CLI**      | Click |
| **Testing**  | Pytest, HTTPX |

---

## Features

- **Rails-like structure**: `config/` for settings and routes, `app/controllers`, `app/models`, `app/services`, `app/jobs`, concerns/mixins.
- **Central routing**: Single `config/routes.py` with `resources()` and `namespace()` helpers.
- **Base controller**: `@before_action` / `@after_action`, `render_json` / `render_error`, `params`, `current_user`.
- **Base model**: Callbacks (`@before_save`, `@after_create`, etc.), `save` / `destroy` / `update` / `to_dict` / `reload`, scopes (`find`, `find_by`, `where`, `all`, `create`).
- **Model concerns**: Timestampable, SoftDeletable, Sluggable.
- **Controller concerns**: Authenticatable, Paginatable.
- **Services**: Business logic layer with `success()` / `failure()`.
- **Background jobs**: Celery with BaseJob, retries, queues (default, mailers, low_priority), Beat schedule.
- **Auth**: JWT access + refresh tokens, role-based (user, admin, moderator).
- **Migrations**: Timestamped Alembic migrations and CLI generator.
- **CLI**: `manage.py` for server, db, generate, routes, worker, scheduler, shell.

---

## Project structure

```
myapp/
├── main.py                    # FastAPI app entry, lifespan, health check
├── manage.py                  # CLI (runserver, db, generate, routes, worker, shell)
├── alembic.ini                # Alembic config
├── requirements.txt
├── .env.example
│
├── config/
│   ├── __init__.py
│   ├── settings.py            # Pydantic Settings (env vars, Celery config)
│   ├── database.py            # Engine, SessionLocal, Base, get_db
│   ├── celery.py              # Celery app, queues, Beat schedule
│   └── routes.py              # draw_routes, resources(), namespace()
│
├── app/
│   ├── controllers/           # Request handlers + filters
│   │   ├── base_controller.py
│   │   ├── concerns/          # Authenticatable, Paginatable
│   │   ├── users_controller.py
│   │   ├── posts_controller.py
│   │   └── auth_controller.py
│   │
│   ├── models/                 # SQLAlchemy models + callbacks
│   │   ├── base_model.py
│   │   ├── concerns/          # Timestampable, SoftDeletable, Sluggable
│   │   ├── user.py
│   │   └── post.py
│   │
│   ├── schemas/               # Pydantic v2 (request/response)
│   │   ├── user_schema.py
│   │   └── post_schema.py
│   │
│   ├── services/              # Business logic
│   │   ├── base_service.py
│   │   ├── user_service.py
│   │   └── post_service.py
│   │
│   ├── jobs/                  # Celery tasks (BaseJob)
│   │   ├── base_job.py
│   │   ├── welcome_email_job.py
│   │   └── cleanup_job.py
│   │
│   ├── middleware/
│   │   ├── auth_middleware.py  # JWT → request.state.current_user
│   │   └── logging_middleware.py
│   │
│   └── helpers/
│       ├── jwt_helper.py      # create_access_token, decode_token, etc.
│       └── response_helper.py # success_response, error_response
│
├── db/
│   ├── migrations/
│   │   ├── env.py             # Alembic env, target_metadata
│   │   └── versions/          # YYYYMMDD_HHMMSS_description.py
│   └── seeds.py               # Seed admin, users, posts
│
└── tests/
    ├── conftest.py            # db, client, authenticated_client, fixtures
    ├── test_health.py
    ├── test_users.py
    ├── test_auth.py
    └── test_posts.py
```

---

## Prerequisites

- **Python** 3.11 or newer  
- **PostgreSQL** (e.g. 14+)  
- **Redis** (for Celery broker and optional cache)

---

## Installation

1. **Clone and enter the project**

   ```bash
   cd myapp
   ```

2. **Create and activate a virtual environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Copy environment file and configure**

   ```bash
   cp .env.example .env
   # Edit .env with your DATABASE_URL, JWT_SECRET_KEY, Redis/Celery URLs, etc.
   ```

---

## Environment configuration

All configuration is driven by environment variables (and `.env`). See `.env.example` for the full list.

| Variable | Description | Default |
|----------|-------------|---------|
| **App** | | |
| `APP_NAME` | Application name | `MyApp` |
| `APP_ENV` | `development` / `staging` / `production` | `development` |
| `DEBUG` | Enable debug mode and /docs, /redoc | `True` |
| `SECRET_KEY` | App secret (sessions, etc.) | — |
| **Database** | | |
| `DATABASE_URL` | PostgreSQL URL | `postgresql://postgres:postgres@localhost:5432/myapp` |
| `DB_POOL_SIZE` | Connection pool size | `10` |
| `DB_MAX_OVERFLOW` | Max overflow connections | `20` |
| **JWT** | | |
| `JWT_SECRET_KEY` | Signing key for tokens | — |
| `JWT_ALGORITHM` | Algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `7` |
| **Redis** | | |
| `REDIS_URL` | Redis URL (cache, etc.) | `redis://localhost:6379/0` |
| **Celery** | | |
| `CELERY_BROKER_URL` | Broker (e.g. Redis) | `redis://localhost:6379/1` |
| `CELERY_RESULT_BACKEND` | Result backend | `redis://localhost:6379/2` |
| **Pagination** | | |
| `DEFAULT_PAGE_SIZE` | Default `per_page` | `20` |
| `MAX_PAGE_SIZE` | Max `per_page` | `100` |

---

## Database

### Migrations (Alembic)

- Migrations live under `db/migrations/versions/` with timestamped names: `YYYYMMDD_HHMMSS_description.py`.
- Each file has `revision`, `down_revision`, `upgrade()`, and `downgrade()`.

**Run pending migrations**

```bash
python manage.py db:migrate
```

**Rollback**

```bash
python manage.py db:rollback              # one step
python manage.py db:rollback --step=3    # three steps
python manage.py db:rollback --to=20240101_000001
```

**Status and history**

```bash
python manage.py db:status
python manage.py db:history
```

**Generate a new migration**

```bash
python manage.py generate migration create_comments_table
# Creates db/migrations/versions/YYYYMMDD_HHMMSS_create_comments_table.py
```

### Seeding

Seeds create an admin user, sample users, and sample posts.

```bash
python manage.py db:seed
```

### Full reset

Drops all migrations, runs them again, then seeds:

```bash
python manage.py db:reset
```

---

## Running the application

**API server (development)**

```bash
python manage.py runserver
# Optional: --port=8080 --host=0.0.0.0
```

- API base: `http://localhost:8000`  
- Health: `http://localhost:8000/health`  
- Swagger (if `DEBUG=True`): `http://localhost:8000/docs`  
- ReDoc: `http://localhost:8000/redoc`

**Celery worker**

```bash
python manage.py worker
# Or a specific queue:
python manage.py worker --queue=mailers
python manage.py worker --queue=low_priority
```

**Celery Beat (scheduled tasks)**

```bash
python manage.py scheduler
```

**Interactive shell (app context)**

```bash
python manage.py shell
# Preloaded: db, User, Post
```

---

## CLI reference

| Command | Description |
|---------|-------------|
| **Server** | |
| `python manage.py runserver` | Start Uvicorn with reload |
| `python manage.py runserver --port=8080` | Custom port |
| **Database** | |
| `python manage.py db:migrate` | Run migrations (`alembic upgrade head`) |
| `python manage.py db:rollback` | Rollback one migration |
| `python manage.py db:rollback --step=N` | Rollback N migrations |
| `python manage.py db:rollback --to=<rev>` | Rollback to revision |
| `python manage.py db:status` | Current migration revision |
| `python manage.py db:history` | Migration history |
| `python manage.py db:seed` | Run `db/seeds.py` |
| `python manage.py db:reset` | Downgrade all → upgrade → seed |
| **Generate** | |
| `python manage.py generate migration <name>` | New timestamped migration |
| `python manage.py generate controller <name>` | New controller in `app/controllers/` |
| `python manage.py generate model <name>` | New model in `app/models/` |
| `python manage.py generate job <name>` | New job in `app/jobs/` |
| `python manage.py generate service <name>` | New service in `app/services/` |
| **Other** | |
| `python manage.py routes` | List all routes (method, path, handler) |
| `python manage.py worker` | Start Celery worker |
| `python manage.py worker --queue=mailers` | Worker for specific queue |
| `python manage.py scheduler` | Start Celery Beat |
| `python manage.py shell` | REPL with db, User, Post |

---

## API reference

All API routes are under the `/api/v1` prefix.

### Response format

**Success**

```json
{
  "success": true,
  "data": { ... },
  "meta": { "page": 1, "per_page": 20, "total": 100, "total_pages": 5, "has_next": true, "has_prev": false }
}
```

`meta` is only present for paginated list endpoints.

**Error**

```json
{
  "success": false,
  "error": "Message",
  "code": 400
}
```

### Authentication

- **Header:** `Authorization: Bearer <access_token>`
- **Login:** `POST /api/v1/auth/login` with `{ "email", "password" }` → returns `access_token` and `refresh_token`.
- **Refresh:** `POST /api/v1/auth/refresh` with `{ "refresh_token" }` → returns new `access_token`.

Public routes (no token): `/health`, `/docs`, `/redoc`, `/api/v1/auth/login`, `/api/v1/auth/register`.

### Route table

| Method | Path | Description |
|--------|------|-------------|
| **Health** | | |
| GET | `/health` | Health check |
| **Auth** | | |
| POST | `/api/v1/auth/login` | Login → tokens |
| POST | `/api/v1/auth/register` | Register → tokens |
| POST | `/api/v1/auth/logout` | Logout (client discards tokens) |
| GET | `/api/v1/auth/me` | Current user (requires auth) |
| POST | `/api/v1/auth/refresh` | New access token from refresh token |
| **Users** | | |
| GET | `/api/v1/users` | List users (paginated, auth) |
| POST | `/api/v1/users` | Create user (auth) |
| GET | `/api/v1/users/{id}` | Get user (auth) |
| PUT | `/api/v1/users/{id}` | Update user (auth) |
| DELETE | `/api/v1/users/{id}` | Delete user (admin only) |
| **Posts** | | |
| GET | `/api/v1/posts` | List posts (paginated, optional `?published=true`) |
| POST | `/api/v1/posts` | Create post (auth) |
| GET | `/api/v1/posts/{id}` | Get post |
| PUT | `/api/v1/posts/{id}` | Update post (owner or admin) |
| DELETE | `/api/v1/posts/{id}` | Soft-delete post (owner or admin) |

### Example: register and list users

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"dev@example.com","name":"Dev User","password":"securepass123"}'

# Response includes access_token; use it for protected routes
export TOKEN="<access_token>"

# List users (paginated)
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/users?page=1&per_page=10"
```

---

## Architecture

### Controllers

- Inherit from `BaseController`; get `request`, `db`, and (after auth) `current_user`.
- Use `@before_action(only=[...], except_list=[...])` to run filters before actions.
- Use `render_json(data, status=200, meta=...)` and `render_error(msg, status=400)` for responses.
- **Concerns:** `Authenticatable` (`authenticate_user`, `require_admin`, `require_owner`), `Paginatable` (`paginate`).

### Models

- Inherit from `BaseModel` (which uses `config.database.Base`).
- **Callbacks:** `@before_save`, `@after_save`, `@after_create`, `@before_destroy`, `@after_destroy`.
- **Instance:** `save(db)`, `destroy(db)`, `update(db, **kw)`, `to_dict()`, `reload(db)`.
- **Class:** `find(db, id)`, `find_by(db, **kw)`, `where(db, **kw)`, `all(db)`, `create(db, **kw)`.
- **Concerns:** Timestampable (created_at/updated_at), SoftDeletable (deleted_at, soft_delete/restore), Sluggable (slug generation).

### Services

- Inherit from `BaseService(db)`; return `self.success(data)` or `self.failure(error)`.
- Encapsulate business logic; used by controllers.

### Jobs

- Inherit from `BaseJob`; implement `perform(**kwargs)`.
- Use `MyJob.perform_later(**kwargs)` to enqueue.
- Configure queue, retries, and (optional) `on_failure` in the job class.
- Celery queues: `default`, `mailers`, `critical`, `low_priority`.
- Beat runs `CleanupJob` daily (e.g. 2:00 UTC) for soft-deleted posts older than 30 days.

### Routing

- All routes are defined in `config/routes.py`.
- `draw_routes(app)` registers routes; uses `namespace(app, "/api/v1")` and `resources(router, "/users", UsersController)` (and similarly for posts).
- Routes run `before_actions` then the controller action; path params are passed via `request.state.path_params`.

---

## Testing

Tests use an in-memory SQLite database by default (override with `TEST_DATABASE_URL`).

**Run all tests**

```bash
pytest tests/ -v
```

**Run with coverage**

```bash
pip install pytest-cov
pytest tests/ -v --cov=app --cov-report=term-missing
```

**Fixtures (in `conftest.py`)**

- `db` — Fresh DB session per test; creates/drops tables.
- `client` — `TestClient` with `get_db` overridden to use test DB.
- `sample_user` — Regular user (`user@example.com` / `password123`).
- `admin_user` — Admin (`admin@example.com` / `Admin1234!`).
- `sample_post` — Post belonging to `sample_user`.
- `authenticated_client` — Client with `Authorization: Bearer <token>` for `sample_user`.

**Test modules**

- `test_health.py` — GET `/health`.
- `test_auth.py` — Register, login, me, refresh.
- `test_users.py` — List (401 when unauthenticated), create, get, update, delete (admin vs non-admin).
- `test_posts.py` — List, get, create, update, soft delete.

---

## Background jobs

### Queues

| Queue | Use case |
|-------|----------|
| `default` | General tasks |
| `mailers` | Email (e.g. WelcomeEmailJob) |
| `critical` | High priority |
| `low_priority` | Cleanup, batch (e.g. CleanupJob) |

### Built-in jobs

- **WelcomeEmailJob** — Enqueued after user creation; queue `mailers`, retries 5.
- **CleanupJob** — Permanently deletes soft-deleted posts older than 30 days; queue `low_priority`; scheduled daily via Beat.

### Running workers

```bash
# Default queue
python manage.py worker

# Specific queue
python manage.py worker --queue=mailers
python manage.py worker --queue=low_priority

# Beat (scheduler)
python manage.py scheduler
```

Or with Celery directly:

```bash
celery -A config.celery worker -l info
celery -A config.celery beat -l info
```

---

## Deployment

1. **Environment**
   - Set `APP_ENV=production`, `DEBUG=false`.
   - Use strong, unique `SECRET_KEY` and `JWT_SECRET_KEY`.
   - Point `DATABASE_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, and `REDIS_URL` to production instances.

2. **Processes**
   - Run the API with a process manager (e.g. Gunicorn + Uvicorn worker):  
     `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000`
   - Run one or more Celery workers and one Beat process (or use a separate scheduler if preferred).

3. **Database**
   - Run migrations on deploy: `python manage.py db:migrate`.
   - Optionally run seeds once: `python manage.py db:seed`.

4. **Security**
   - Restrict CORS in production (configure `allow_origins` in `main.py` from settings).
   - Use HTTPS and secure cookies if you add session-based features later.

---

## License

Use this boilerplate as a base for your own projects. Adjust naming, branding, and licensing as needed.
