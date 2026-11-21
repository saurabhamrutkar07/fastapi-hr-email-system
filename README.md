# ColdReach: HR Contacts & Cold Email Platform

A full-stack web app for job seekers to keep a shared list of HR / recruiter
contacts and send them personalised cold emails, with their resume attached,
from their own Gmail account.

**Live:** https://saurabhamrutkar.com

- **Backend:** FastAPI (async), PostgreSQL, SQLAlchemy 2, Alembic
- **Frontend:** React 19, Vite, Tailwind CSS v4
- **Infra:** Docker Compose, Nginx, AWS EC2 + S3, Cloudflare DNS, Let's Encrypt, GitHub Actions CI

---

## Features

**Accounts and security**
- Sign up with email OTP, log in with password or Google (OAuth 2.0)
- Short-lived access token in memory, refresh token in an HttpOnly, Secure cookie
- A password reset signs out every other session
- Roles: user and admin. Admins can block or unblock users and change roles
- Rate limits on login, OTP and email-sending endpoints

**HR contacts**
- One shared contact list; a contact can have several emails and phone numbers
- Search, company filter, paging
- Admins can edit, delete and import contacts from Excel / CSV / ODS

**Sending emails**
- Each user connects their own Gmail with an app password (stored encrypted)
- Email templates with variables (Jinja2), live preview
- Resume upload to S3; the active resume is attached as `<Name>_Resume.pdf`
- Sender profiles (job role, skills, experience) fill the template
- Review every email before sending, up to 50 per batch, sent in the background
- Contacts already emailed are marked and skipped by "select all"
- Admin test mode: only send to an allow-list while testing

**History and dashboard**
- Every sent email is saved with its subject, body, template and resume version
- Filters by status, search and date range; 14-day chart on the dashboard

---

## Architecture

```
            Browser
               │  HTTPS
               ▼
   ┌───────────────────────── EC2 (Docker Compose) ─────────────────────────┐
   │                                                                        │
   │   web: Nginx ──────── serves the React build                           │
   │        │   /api/*                                                      │
   │        ▼                                                               │
   │   api: FastAPI (uvicorn) ───────► db: PostgreSQL 17 (volume)           │
   │        │                                                               │
   └────────┼───────────────────────────────────────────────────────────────┘
            ├──► Gmail SMTP     (each user's own account)
            ├──► AWS S3         (resumes + database backups, via the EC2 IAM role)
            └──► Google OAuth   (sign in with Google)
```

- Nginx terminates TLS (Let's Encrypt), redirects HTTP to HTTPS and `www` to the apex domain.
- Database migrations run on container start (`alembic upgrade head`).
- The API docs (`/docs`, `/redoc`, `/openapi.json`) are turned off when `APP_ENV=production`.

---

## Run it locally

### Option 1: Docker (closest to production)

Needs Docker Desktop.

```bash
cp .env.example .env        # then fill in your values, see "Environment variables"
docker compose up --build
```

Open http://localhost:8080. The database starts empty and is migrated automatically.

### Option 2: Without Docker (for development)

Needs Python 3.12, Node 22 and a local PostgreSQL.

```bash
# Backend (http://localhost:8000, docs at /docs)
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (http://localhost:3000), in another terminal
cd frontend
npm ci
npm run dev
```

---

## Tests and CI

```bash
pytest            # 110 tests, needs TEST_DATABASE_URL pointing at a database whose name ends in _test
cd frontend && npm run lint && npm run build
```

GitHub Actions (`.github/workflows/ci.yml`) runs the backend tests against a
PostgreSQL service container and lints + builds the frontend on every push
and on every pull request into `main`. `main` is protected: changes go through a pull request
and both checks must pass.

---

## Deployment

The app runs on a single AWS EC2 instance (Ubuntu 24.04, t3.small, Mumbai)
with Docker Compose. The server is started only when needed, so its public
IP changes on every start.

| Piece | How |
|---|---|
| App | `docker compose up -d --build` with `docker-compose.prod.yml` (adds HTTPS) |
| HTTPS | Let's Encrypt certificate via certbot, auto-renewed |
| DNS | Cloudflare. On every boot the server updates its own A record ([deploy/cloudflare-ddns.sh](deploy/cloudflare-ddns.sh), run by a systemd service) |
| AWS access | EC2 IAM role for S3, no access keys on the server |
| Backups | [scripts/backup.sh](scripts/backup.sh): `pg_dump` to S3 every 3 hours (cron) and before every stop; S3 deletes backups after 30 days |
| Start / stop | [scripts/server.ps1](scripts/server.ps1) from the laptop: `start`, `stop` (backup first), `status`, `ssh`. Uses an IAM user that can only start/stop this one server ([deploy/iam-laptop-policy.json](deploy/iam-laptop-policy.json)) |

Deploying a change: merge the pull request, then on the server
`git pull && docker compose up -d --build`.

---

## Environment variables

Put these in a `.env` file in the project root. Never commit it.

| Variable | Required | What it is |
|---|---|---|
| `DATABASE_URL` | yes (not with Docker) | `postgresql+asyncpg://user:pass@host:5432/db`. Docker Compose builds it for you |
| `POSTGRES_PASSWORD` | with Docker | Password for the Postgres container |
| `JWT_SECRET_KEY` | yes | Long random string, signs login tokens |
| `ENCRYPTION_KEY` | yes | Fernet key, encrypts saved Gmail app passwords. Keep the same key when you move the database |
| `EMAIL_ADDRESS`, `EMAIL_PASSWORD` | yes | Gmail account and app password that send OTP emails |
| `S3_BUCKET_NAME`, `AWS_REGION` | yes | Bucket for resumes |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | laptop only | Set both or neither. On EC2 leave them out, the IAM role is used |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | yes | Google OAuth client |
| `GOOGLE_REDIRECT_URI`, `FRONTEND_URL` | without Docker | e.g. `http://localhost:8000/auth/google/callback` and `http://localhost:3000` |
| `PUBLIC_URL` | with Docker | Public address, e.g. `https://saurabhamrutkar.com`. Sets the two above |
| `APP_ENV` | no | `production` turns off the API docs. Default `development` |
| `COOKIE_SECURE` | no | `true` (default) sends cookies only over HTTPS. `false` for plain-HTTP local use |
| `WEB_PORT` | no | Port Nginx listens on with Docker. Default `8080` |
| `SENTRY_DSN` | no | Error reporting. Off when empty |
| `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`, `DB_POOL_RECYCLE`, `DB_STATEMENT_TIMEOUT_MS`, `DB_ECHO` | no | Database pool tuning |
| `RATE_LIMIT_ENABLED` | no | `false` turns rate limits off (tests) |

---

## Project structure

```
app/
├── api/            Route handlers (auth, users, hr_contacts, email, templates, resumes, ...)
├── core/           Config, security (JWT), encryption, mailer, S3, rate limits, request id, Sentry
├── database/       Engine, session, repositories
├── models/         SQLAlchemy models
├── schemas/        Pydantic request / response models
├── services/       Business logic (sending, history, admin users, Excel import)
└── main.py         App, middleware, routers
migrations/         Alembic migrations
tests/              pytest suite
frontend/           React app (pages, components, api clients) + Nginx config
deploy/             Production Nginx config, Cloudflare DNS update, IAM policy
scripts/            backup.sh (server), server.ps1 (laptop start/stop)
Dockerfile, docker-compose.yml, docker-compose.prod.yml
```

---

## Roadmap

- Continuous deployment from GitHub Actions
- Monitoring and uptime alerts
- Scheduled sending (pick a date and time)
- Reply tracking over IMAP and follow-up reminders

---

## Author

**Saurabh Sunil Amrutkar**, Python Backend Developer
