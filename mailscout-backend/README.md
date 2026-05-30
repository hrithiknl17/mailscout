# MailScout

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com)

**Free, open-source email verification SaaS — an alternative to Hunter.io and NeverBounce.**

---

## Why I built this

Hunter.io charges $34/month for what's essentially a 500-line script doing DNS lookups + SMTP handshakes. After my own cold-email campaign had a 40% bounce rate because of bad email guesses, I decided to learn the protocol and build my own. MailScout is the result — same core functionality, MIT-licensed, self-hostable.

---

## Architecture

```
┌────────────────┐   HTTPS    ┌──────────────────────────────────┐
│   Frontend     │ ─────────► │         FastAPI :8000            │
│  (Session 2)   │ ◄───────── │   Auth middleware → Routers      │
└────────────────┘            └────────────────┬─────────────────┘
                                               │
                              ┌────────────────▼─────────────────┐
                              │       Verification Engine         │
                              │                                   │
                              │  [1] Syntax (email-validator)     │
                              │  [2] DNS A-record (socket)        │
                              │  [3] MX records (dnspython)       │
                              │  [4] SMTP handshake (aiosmtplib)  │
                              └────────┬──────────────┬───────────┘
                                       │              │
                          ┌────────────▼───┐  ┌───────▼──────────┐
                          │ Supabase Postgres│  │      Redis       │
                          │ verifications   │  │  MX cache 24h    │
                          │ jobs            │  │  catch-all 7d    │
                          └─────────────────┘  └──────────────────┘
```

---

## Running frontend + backend together

### Prerequisites
- Backend: Python 3.11+, Docker (for Redis + Postgres), a Supabase project
- Frontend: Node.js 18+

### Step 1 — Backend

```bash
cd mailscout/mailscout-backend
cp .env.example .env          # fill in SUPABASE_URL, keys, DATABASE_URL, REDIS_URL

docker compose up db redis -d  # start Postgres + Redis locally
# OR point DATABASE_URL / REDIS_URL at remote services

uvicorn app.main:app --reload --port 8000
```

### Step 2 — Frontend

```bash
cd mailscout/frontend
cp .env.local.example .env.local
# Fill in:
#   NEXT_PUBLIC_SUPABASE_URL     (same project as backend)
#   NEXT_PUBLIC_SUPABASE_ANON_KEY
#   NEXT_PUBLIC_API_URL=http://localhost:8000

npm install
npm run dev                    # starts at http://localhost:3000
```

Open `http://localhost:3000`. Sign up → verify emails → upload CSVs.

### Run frontend tests

```bash
cd frontend
npm test
```

---

## Quick start

### Docker (recommended)

```bash
git clone https://github.com/hrithiknl17/mailscout
cd mailscout/mailscout-backend

cp .env.example .env
# Edit .env — add your Supabase URL + keys

docker compose up --build
```

API available at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

### Local dev (uvicorn)

```bash
cd mailscout-backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Start local Postgres + Redis
docker compose up db redis -d

# Apply schema to your Supabase project
# → Paste migrations/001_initial.sql into Supabase SQL Editor

cp .env.example .env  # fill in values
uvicorn app.main:app --reload
```

### Run tests

```bash
pytest
```

All tests mock network calls — they run offline, no real DB or SMTP needed.

---

## The 4-layer verification pipeline

Every email address goes through four layers in sequence. Each layer can short-circuit.

### Layer 1 — Syntax (RFC 5322)

Uses `email-validator` to check format. Catches typos, missing `@`, invalid TLDs.

```
user@example.com     → pass
user@example         → ✗ invalid_syntax
@example.com         → ✗ invalid_syntax
```

### Layer 2 — Domain A record

Resolves `socket.gethostbyname(domain)`. If the domain doesn't resolve, no mail server can exist.

```
example.com          → resolves → pass
fakexyz12345.io      → NXDOMAIN → ✗ dead_domain
```

### Layer 3 — MX records

Queries DNS for MX records via `dnspython`. Results cached in Redis for 24h.

```
example.com  → MX: mail.example.com (priority 10) → pass
nodns.co     → no MX records                       → ✗ no_mail_server
```

### Layer 4 — SMTP handshake (3 sub-checks)

**4a — Accept-all provider detection**

Gmail, Outlook, Yahoo, iCloud, ProtonMail, and domains whose MX points to Google/Microsoft/Yahoo infrastructure never return reliable SMTP responses. We detect them and return `risky` immediately.

```
user@gmail.com   → risky (confidence 0.5)
user@company.com using Google Workspace → risky (MX ends in .google.com)
```

**4b — Catch-all detection**

Before checking the real address, probe with a guaranteed-fake one:
`definitely-fake-mailbox-xyz789@domain.com`

If the server says 250 (accepted), the domain accepts everything — verifying the real address is pointless. Cached for 7 days.

```
fake-xyz@acme.com → 250 → domain is catch-all → all addresses risky (confidence 0.6)
```

**4c — SMTP probe**

Connect to the primary MX on port 25. HELO, MAIL FROM, RCPT TO. Parse the response. QUIT immediately — we never send a message body.

```
RCPT TO:<user@example.com>
250 OK          → deliverable (confidence 0.95)
550 No such user → undeliverable (confidence 0.95)
421 Try again   → temporary_failure → retry once → unknown if still failing
```

---

## API reference

All endpoints except `/health` require `Authorization: Bearer <supabase_jwt>`.

### Health check

```bash
curl http://localhost:8000/health
# {"status":"ok","version":"1.0.0","checks":{"db":"ok","redis":"ok"}}
```

### Verify single email

```bash
curl -X POST http://localhost:8000/api/verify/single \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com"}'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john@example.com",
  "status": "deliverable",
  "confidence": 0.95,
  "reason": "SMTP 250 OK",
  "mx_record": "mail.example.com",
  "is_catch_all": false,
  "is_disposable": false,
  "is_role": false,
  "created_at": "2026-05-20T10:30:00Z"
}
```

Status values: `deliverable` | `undeliverable` | `risky` | `invalid_syntax` | `dead_domain` | `no_mail_server` | `temporary_failure` | `unknown`

### Verify bulk (CSV or TXT)

```bash
# CSV with 'email' column
curl -X POST http://localhost:8000/api/verify/bulk \
  -H "Authorization: Bearer $JWT" \
  -F "file=@emails.csv"

# Plain TXT (one email per line)
curl -X POST http://localhost:8000/api/verify/bulk \
  -H "Authorization: Bearer $JWT" \
  -F "file=@emails.txt"
```

Response (immediate):
```json
{"job_id": "abc123...", "total": 250, "status": "queued"}
```

### Get job status

```bash
curl http://localhost:8000/api/jobs/$JOB_ID \
  -H "Authorization: Bearer $JWT"
```

```json
{
  "id": "abc123...",
  "status": "completed",
  "total_emails": 250,
  "processed": 250,
  "deliverable_count": 180,
  "risky_count": 40,
  "undeliverable_count": 20,
  "dead_domain_count": 5,
  "unknown_count": 5,
  "created_at": "2026-05-20T10:00:00Z",
  "completed_at": "2026-05-20T10:05:00Z",
  "result_csv_url": null
}
```

### Verification history

```bash
curl "http://localhost:8000/api/history?limit=20&offset=0" \
  -H "Authorization: Bearer $JWT"
```

### Usage stats

```bash
curl http://localhost:8000/api/usage \
  -H "Authorization: Bearer $JWT"
# {"used_this_month": 47, "monthly_limit": 100, "renews_at": "2026-06-01"}
```

---

## Database schema

Run `migrations/001_initial.sql` in the Supabase SQL Editor. Row-Level Security is enabled — users can only read their own rows even with the anon key.

---

## Known limitations

**Gmail / Outlook / Yahoo always return `risky`.**
These providers reject SMTP probing — any RCPT TO returns 250 regardless of whether the mailbox exists. This isn't a MailScout limitation; no commercial verifier can bypass this either (Hunter.io, NeverBounce, and ZeroBounce all have the same problem and charge you anyway).

**Port 25 is blocked on most residential ISPs.**
You'll get `unknown` for everything on a home network. Deploy to a cloud VM (EC2, DigitalOcean, Fly.io) that allows outbound port 25. Layer 1–3 checks (syntax, DNS, MX) still work anywhere.

**Catch-all detection is probabilistic.**
Some servers accept fake addresses silently to prevent enumeration but reject real ones at delivery time. There's no way to distinguish this without sending an actual email.

**No disposable-address detection in V1.**
The `is_disposable` field is present in the schema and always returns `false`. Integration with a disposable domain list (e.g., disposable.github.io) is planned for V2.

---

## Deployment

### Railway

```bash
railway login
railway init
railway up
railway variables set DATABASE_URL=... REDIS_URL=... SUPABASE_URL=... ...
```

### Fly.io

```bash
fly launch
fly secrets set DATABASE_URL=... REDIS_URL=... SUPABASE_URL=... ...
fly deploy
```

### AWS EC2 (free tier)

1. Launch a `t2.micro` (Amazon Linux 2023).
2. Allow inbound 8000 (API) and outbound 25 (SMTP probing).
3. Install Docker + Docker Compose, clone repo, `docker compose up -d`.
4. Port 25 on EC2 is restricted by default — submit the AWS request form to lift it.

---

## Performance benchmarks

TBD — will be filled in after Session 3 (load testing with Locust).

---

## Contributing

1. Fork the repo
2. Create a branch: `git checkout -b feat/your-feature`
3. Add tests for new verification logic
4. Run `pytest` — all tests must pass offline
5. Open a PR

---

## License

MIT — see [LICENSE](../LICENSE).

Built by [Hrithik N L](https://github.com/hrithiknl17).
