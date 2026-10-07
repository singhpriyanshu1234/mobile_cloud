# Scalability — from one phone to the cloud

## Current (v1, this repo)

```
Client → FastAPI (gateway middleware in-process) → SQLite file
```

One process, one file, in-memory rate limits. Fine for a demo;
everything is stateless except the DB file and the limiter buckets.

## Future (production shape)

```
                    ┌───────────────┐
                    │ Load Balancer │
                    └───────┬───────┘
                            │
               ┌────────────┼────────────┐
               ▼            ▼            ▼
            API-1        API-2        API-3   (stateless FastAPI replicas)
               │            │            │
               └────────────┼────────────┘
                            │
                     PostgreSQL (primary + read replicas)
                            │
                         Redis (cache + rate limits + token denylist)
                            │
                     Message Queue (welcome emails, audit, webhooks)
```

## 1. Horizontal scaling

Run N identical API containers; no local state except config. JWT
verification needs only `SECRET_KEY`, so any replica can serve any
request. Scale replicas on CPU/latency/request-queue metrics.

## 2. Load balancing

A Layer-7 balancer (NGINX, AWS ALB) spreads HTTP across replicas and
runs `/api/health` checks to drain unhealthy ones. Sticky sessions are
*not* needed because the API is stateless.

## 3. Database scaling

- SQLite → PostgreSQL (concurrent writers, real types, `FOR UPDATE`).
- Read replicas for profile reads; primary for writes.
- Later: sharding by `user_id` hash if a single primary saturates.

## 4. Connection pooling

Replace one-connection-per-request with a pool (e.g. PgBouncer or
SQLAlchemy `QueuePool` with `pool_size=20, max_overflow=10`) so bursts
reuse connections instead of paying TCP+TLS+auth setup each time.

## 5. Redis caching

Cache `GET /api/users/me` (`user:{id}` key, TTL ~60s, invalidate on
`PUT`/`DELETE`). Cache health rarely; never cache auth decisions
beyond the JWT itself. Expected win: profile reads skip the DB entirely.

## 6. Distributed rate limiting

The current `dict` of timestamps lives in one process — with 3 replicas
an attacker gets 3× the budget and restarts wipe counters. Production:
Redis atomic counters per `key = endpoint:ip` with expiry
(`INCR` + `EXPIRE`, or a token-bucket Lua script).

## 7. Message queues

Move side effects off the request path: signup publishes
`user.registered`; workers send welcome email, write audit log, warm
caches. Queue (SQS/RabbitMQ/Kafka) gives retries + backpressure so a
slow mail server never slows signup.

## 8. Stateless services

Rules already followed here: no server sessions, JWT carries identity,
uploads (if added) go to object storage not local disk. Any replica can
die and no user data is lost.

## 9. Health checks

- Liveness `GET /api/health` → process alive?
- Readiness `GET /api/health/database` → DB + (later) Redis reachable?
- Orchestrator (K8s/compose) restarts liveness failures, stops routing
  to readiness failures.

## 10. Monitoring

Metrics: request rate, p50/p95 latency, 5xx rate, login failure rate,
DB pool usage, CPU/mem per replica. Alerts on 5xx spike, p95 breach,
DB down. Dashboards per endpoint.

## 11. Logging

Today: one human-readable line per request (ID, method, path, status,
duration). Production: JSON logs → collector (Loki/ELK) with the same
`request_id` propagated to services/queue workers for end-to-end traces.

## 12. Fault tolerance

- Timeouts + retries with jitter on DB/Redis/queue calls.
- Circuit breakers: fail fast to cached profile or 503 + `Retry-After`
  when the DB is saturated.
- Graceful shutdown: drain in-flight requests before exit.
- Backups: nightly PostgreSQL snapshots + tested restore.
- Chaos basics: kill a replica mid-demo — balancer reroutes, user retries
  safely (signup/login/profile writes are idempotent or guarded).
