# Scalable User Authentication & Management Platform

A **system-design demonstration**: a working full-stack auth app (HTML/CSS/JS +
FastAPI + SQLite + JWT) structured like the first version of a production
system — gateway middleware, service/data layering, health checks, rate
limiting — and runnable on an **Android phone via Termux**.

## Quick run (laptop / PC)

```bash
cd scalable-auth-platform
pip install -r requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Open http://127.0.0.1:8000

## Run on Android (Termux) — exact steps

1. Install Termux from F-Droid / GitHub releases (Play Store build is outdated).
2. Allow Wi-Fi access; connect the phone and your laptop to the **same Wi-Fi**.
3. In Termux:

```bash
pkg update
pkg install python git -y
git clone <your-repository-url>
cd scalable-auth-platform
pip install --upgrade pip
pip install -r requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### If you see "Failed building wheel for pydantic-core"

This is expected on some Termux setups: `pydantic-core` (a Rust
extension used by Pydantic v2) has no prebuilt package for Android, so
pip tries to compile it from source and fails. Everything else in this
project is pure Python — only Pydantic is affected. Fix (no Rust, no
waiting, installs in seconds):

```bash
pip install -r requirements-termux.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

This pins Pydantic v1 (pure Python). FastAPI supports both v1 and v2,
and the app code is compatible with both — it was tested end-to-end
(signup, login, JWT profile, update, delete) on each.

Alternatives: `pkg install rust` and retry the normal requirements
(~10-minute build, large download), or use `uv` with the Termux PyPI
mirror for prebuilt wheels.

> `--host 0.0.0.0` is required — it listens on all interfaces. `127.0.0.1`
> alone would only be reachable from the phone itself.

4. Find the phone's local IP. In Termux run:

```bash
ifconfig wlan0 | grep inet
# or
ip addr show wlan0
```

Look for something like `192.168.1.10` (ignore `127.0.0.1`).

5. On the **laptop browser** (same Wi-Fi), open:

```
http://PHONE_IP:8000
```

Example: `http://192.168.1.10:8000`

6. On the phone itself, open `http://127.0.0.1:8000` in a mobile browser.

If the laptop can't connect: disable AP isolation / client isolation on the
router, allow port 8000 through any firewall, and confirm both devices share
the same subnet (`192.168.1.x`).

## What to click

1. `Sign Up` → create an account (try a duplicate email to see the 409 path).
2. `Login` → JWT is stored, you land on `/dashboard.html`.
3. `Dashboard` → profile data + live API/DB health.
4. `Profile` → rename yourself, then delete the account.
5. Wrong password × 11 within a minute → `429 RATE_LIMITED` (login limiter).

Interactive API docs: `http://PHONE_IP:8000/docs`

## Layout

```
frontend/   static HTML/CSS/vanilla JS (served by FastAPI)
backend/    main.py (app + gateway wiring)
            api/        thin HTTP routes (auth, users, health)
            services/   business rules (auth_service, user_service)
            database/   engine/session + SQLAlchemy User model
            models/     Pydantic schemas + User re-export
            middleware/ logging (request ID + timing) + rate limiting
            utils/      config (env) + password/JWT crypto
docs/       architecture, api-design, database-design, scalability
```

## Configuration

Copy `.env.example` to `.env` to override defaults:

| Var | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | dev default | JWT signing key — **change in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 60 | Token lifetime |
| `DATABASE_URL` | `sqlite:///./auth.db` | Swap to Postgres later |
| `RATE_LIMIT_PER_MINUTE` | 100 | General API budget per IP |
| `LOGIN_RATE_LIMIT_PER_MINUTE` | 10 | Login budget per IP |

## Security notes (demo trade-offs)

- Passwords hashed with pbkdf2_sha256 (pure-Python, Termux-safe); hashes
  never leave the server.
- JWT in `localStorage` is fine for a demo but XSS-readable — production
  should use httpOnly cookies + CSRF tokens, short-lived access tokens +
  refresh rotation, and HTTPS everywhere.
- CORS is `*` for the local demo; restrict to real origins in production.

## Real today vs. conceptual/future

Real in this repo: browser client, in-process gateway middleware, auth
service, user service, SQLite via SQLAlchemy, in-memory rate limiter,
request logging, health probes, standardized errors.

Conceptual (documented, not deployed): external API gateway / load
balancer, Redis (distributed limits, cache, token denylist), Postgres
with pooling/replicas, message queue, metrics/tracing, multi-replica
deploys. See `docs/scalability.md`.
