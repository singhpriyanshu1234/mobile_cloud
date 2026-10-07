# Database Design

## Engine choice

- Today: **SQLite** file (`auth.db`) via SQLAlchemy. Zero setup, works on
  Termux, single-writer friendly for a demo.
- Later: **PostgreSQL** by changing `DATABASE_URL` and installing a driver
  (`psycopg2`). No frontend or service-signature changes needed because all
  SQL lives behind the service/repository layer (`services/*` + SQLAlchemy).

## Schema

```sql
CREATE TABLE users (
    id            INTEGER PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active     BOOLEAN NOT NULL DEFAULT 1
);
CREATE UNIQUE INDEX ix_users_email ON users (email);
```

| Column | Why |
|---|---|
| `id` | Integer PK, returned as `sub` in JWT and in profile payloads |
| `name` | Display name, editable via `PUT /api/users/me` |
| `email` | Login identity; **unique**; always stored lowercase/trimmed |
| `password_hash` | pbkdf2_sha256 hash — **never returned by any API** |
| `created_at` / `updated_at` | Audit + shown on dashboard; `updated_at` auto-bumps |
| `is_active` | Kill-switch: login + token validation reject inactive users; reserved for future soft-delete/ban |

## Constraints & indexes

- `UNIQUE(email)` enforces one account per email at the DB level (the app
  also pre-checks to return a friendly 409).
- Index on `email` makes login lookups O(log n).
- Index on `id` (PK) makes per-request token→user loads fast.

## Access pattern

```
API route --Depends(get_db)--> Session --> service function
--> db.query(User)... --> commit/refresh --> Pydantic response
```

- One SQLAlchemy `Session` per request (see `database/database.py:get_db`).
- Services own all queries; routes never write SQL.
- `GET /health/database` runs `SELECT 1` as a connectivity probe.

## Migration path to PostgreSQL

1. Set `DATABASE_URL=postgresql://user:pass@host:5432/authdb`.
2. `pip install psycopg2-binary`; remove SQLite `check_same_thread` arg
   (already conditional in code).
3. Add Alembic for migrations (today `Base.metadata.create_all` is enough).
4. Enable connection pooling (`pool_size`, `max_overflow`) — see
   `docs/scalability.md`.
