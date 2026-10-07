# API Design

Base URL (local): `http://<PHONE_IP>:8000`
All responses use the envelope:

```json
{ "success": true, "data": { } }
{ "success": false, "error": { "code": "SOME_CODE", "message": "human text" } }
```

Auth: `Authorization: Bearer <JWT>` header for every protected endpoint.

## POST /api/auth/signup

- Purpose: register a new user.
- Auth: none.
- Body: `{ "name": "Asha", "email": "asha@example.com", "password": "secret123" }`
- 201 response: `{success, data: {user: {id, name, email, created_at, is_active}, access_token, token_type}}`
- Errors: 400 `NAME_REQUIRED` / `INVALID_EMAIL` / `WEAK_PASSWORD`, 409 `EMAIL_EXISTS`.

## POST /api/auth/login

- Purpose: verify credentials, issue JWT. Rate-limited to 10/min per IP.
- Auth: none.
- Body: `{ "email": "...", "password": "..." }`
- 200 response: same shape as signup.
- Errors: 401 `INVALID_CREDENTIALS`, 429 `RATE_LIMITED`.

## POST /api/auth/logout

- Purpose: stateless logout signal (client discards token).
- Auth: none required.
- 200: `{success, data: {message}}`.

## GET /api/auth/me

- Purpose: return the caller from its JWT.
- Auth: required.
- 200: `{success, data: {user}}`.
- Errors: 401 `NOT_AUTHENTICATED` / `INVALID_TOKEN`.

## GET /api/users/me

- Purpose: get own profile (User Service read path).
- Auth: required.
- 200: `{success, data: {user}}`.

## PUT /api/users/me

- Purpose: update own display name.
- Auth: required.
- Body: `{ "name": "New Name" }`
- 200: `{success, data: {user}}`.
- Errors: 400 `NAME_REQUIRED`, 404 `NOT_FOUND`.

## DELETE /api/users/me

- Purpose: permanently delete own account.
- Auth: required.
- 200: `{success, data: {message}}`.
- Errors: 404 `NOT_FOUND`.

## GET /api/health

- Purpose: liveness probe (is the API process up?).
- Auth: none.
- 200: `{ "status": "healthy" }`.

## GET /api/health/database

- Purpose: readiness probe (can we reach the DB?).
- Auth: none.
- 200 healthy: `{ "status": "healthy", "database": "online" }`.
- 200 unhealthy: `{ "status": "unhealthy", "database": "offline" }`.

## Status codes used

| Code | Meaning |
|---|---|
| 200 | OK (login, logout, reads, updates, deletes, health) |
| 201 | Created (signup) |
| 400 | Bad input (validation) |
| 401 | Missing/invalid credentials or token |
| 404 | User not found |
| 409 | Email already registered |
| 429 | Rate limit exceeded |
| 500 | Unexpected fault (generic message, details in server log) |
