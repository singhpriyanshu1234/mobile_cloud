# Architecture — Scalable User Authentication & Management Platform

## 1. Problem statement

We need a user system (signup, login, profile, delete) that starts as a
tiny demo runnable on one Android phone, but is structured so it can grow
into a horizontally scaled cloud system without a rewrite.

## 2. Requirements

- Must run on Termux (Android) with only Python + `pip install -r requirements.txt`.
- Must be reachable from another device on the same Wi-Fi.
- Must demonstrate: gateway, service separation, JWT auth, DB design,
  rate limiting, logging, health checks, fault handling.

## 3. Functional requirements

1. Signup with name/email/password.
2. Login returning a JWT.
3. Logout (client discards token; stateless server).
4. View own profile (`GET /api/auth/me`, `GET /api/users/me`).
5. Update own name (`PUT /api/users/me`).
6. Delete own account (`DELETE /api/users/me`).
7. Health probes (`GET /api/health`, `GET /api/health/database`).

## 4. Non-functional requirements

- Beginner-readable code, but with production-style layering.
- No plaintext passwords; no hashes in API responses.
- Standardized errors, no secret leakage.
- Basic abuse protection (rate limits) and observability (logs, health).
- Stateless API processes so more instances can be added later.

## 5. Architecture

```
Client (browser: HTML/CSS/vanilla JS)
   ↓  HTTP + JWT (Authorization: Bearer <token>)
API Gateway (in-process FastAPI middleware: logging, request ID,
             rate limiting, CORS, standardized errors)
   ↓
Authentication Service (backend/services/auth_service.py)
User Service         (backend/services/user_service.py)
   ↓  (repository pattern: services -> SQLAlchemy -> DB)
Database (SQLite file today; PostgreSQL later)
```

Route map:

- `backend/main.py` — app wiring, gateway middleware, static frontend.
- `backend/api/*.py` — thin HTTP layer (parse/validate/respond).
- `backend/services/*.py` — business rules (validation, hashing, JWT).
- `backend/database/*` — engine, session, ORM models.
- `backend/middleware/*` — gateway cross-cutting concerns.
- `backend/utils/*` — config + cryptography.

## 6. Component responsibilities

| Component | Owns | Does NOT own |
|---|---|---|
| Client | Forms, token storage, redirects | Any secret validation |
| API Gateway (middleware) | Request ID, timing, logs, rate limits, error envelope | Business rules |
| Auth Service | Signup/login validation, hashing, JWT issue/verify | Profile edits |
| User Service | Get/update/delete profile | Passwords, tokens |
| Database layer | Schema, sessions, queries | HTTP, auth logic |

## 7. Data flow (generic protected request)

```
Client → JWT → Gateway (ID, log, rate-limit) → route →
dependency get_current_user (decode JWT → load user) →
service (business rule) → SQLAlchemy → SQLite → JSON response
```

## 8. Authentication flow (JWT)

1. Login verifies password with `passlib` (pbkdf2_sha256).
2. Server signs `{sub: user_id, iat, exp}` with `SECRET_KEY` (HS256).
3. Client stores token, sends `Authorization: Bearer <token>`.
4. `get_current_user` decodes the signature, checks expiry, loads the
   user, rejects inactive/missing users with 401.
5. No server-side session is stored → any instance can validate any token.

## 9. Signup flow

```
Client → Gateway → Auth Service → validate input → check duplicate email
→ hash password → User Repository (INSERT) → Database
→ issue JWT → Response {user, access_token}
```

## 10. Login flow

```
Client → Gateway (strict 10/min limit) → Auth Service → find user
→ verify password → Generate JWT → Client stores token → /dashboard.html
```

## 11. Request flow (example: PUT /api/users/me)

1. Middleware assigns request ID, starts timer, checks rate bucket.
2. Router parses `UpdateProfileRequest` (Pydantic validates).
3. `get_current_user` authenticates the JWT.
4. `user_service.update_profile` updates the row.
5. JSON `{success: true, data: {user}}` returns; log line records
   method/path/status/duration.

## 12. Failure scenarios

| Failure | Handling |
|---|---|
| Duplicate email | 409 `EMAIL_EXISTS` |
| Bad credentials | 401 `INVALID_CREDENTIALS` (same message either way — no user enumeration) |
| Missing/expired token | 401 `NOT_AUTHENTICATED` / `INVALID_TOKEN` |
| Validation error | 400/422 with field info, no stack trace |
| Rate exceeded | 429 `RATE_LIMITED` |
| DB file locked / down | `/health/database` reports offline; 500 envelope hides internals |
| Crash mid-request | Log line with request ID; generic 500 envelope |
| Phone sleeps / Wi-Fi drops | Client sees fetch failure → status pills show Offline |

## 13. Scalability strategy

See `docs/scalability.md`. Short version: keep services stateless, put
the DB behind a repository interface, move rate limits/caches to Redis,
add a real gateway + load balancer, scale API replicas horizontally.

## 14. Security considerations

- pbkdf2_sha256 password hashing (pure-Python, Termux-safe).
- JWT expiry (default 60 min), server-side `is_active` check on every call.
- Pydantic input validation + normalized lowercase emails.
- CORS open (`*`) for the local demo — restrict to real origins in prod.
- localStorage token is XSS-readable; acceptable for a demo, but a
  production app should use httpOnly cookies + CSRF protection.
- Logs contain only metadata (no passwords/tokens/bodies).

## 15. Future improvements

- PostgreSQL + Alembic migrations, connection pooling.
- Redis: distributed rate limits, token denylist, profile cache.
- Refresh tokens + short-lived access tokens.
- Email verification, password reset, OAuth (Google/GitHub).
- Real gateway (Kong/NGINX/AWS API GW), load balancer, multi-replica deploy.
- Structured JSON logs, metrics (Prometheus), tracing (OpenTelemetry).
- Tests (pytest), CI, Docker image for cloud deploy.
