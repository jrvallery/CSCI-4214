# SkiWare — Contributor Guide

SkiWare is an AI-powered ski damage assessment tool. Users input their ski details and describe an issue — SkiWare returns a safety flag, severity rating, estimated shop cost, DIY repair instructions, a parts checklist, and relevant YouTube guides. See [README.md](README.md) for full project context.

---

## Project Structure

```
SkiWare/
├── backend/
│   ├── main.py              # FastAPI app entrypoint — registers all routers
│   ├── routers/
│   │   ├── assessments.py   # POST /api/assess
│   │   ├── users.py         # User CRUD + auth endpoints
│   │   └── shops.py         # GET /api/shops/nearest
│   ├── services/
│   │   ├── assessment.py    # RAG + Gemini assessment logic
│   │   ├── users.py         # User service logic
│   │   ├── shops.py         # Google Places API + ranking
│   │   └── calculate_DIN.py # DIN binding calculation
│   └── models/
│       ├── assesment.py     # Assessment request/response models
│       ├── user.py          # User Pydantic models
│       └── tables.py        # SQLAlchemy ORM table definitions
├── frontend/
│   └── src/
│       ├── App.jsx          # Root: page state machine + routing
│       ├── App.css          # All styles (single stylesheet)
│       ├── components/
│       │   └── Header.jsx
│       └── pages/
│           ├── HomePage.jsx
│           ├── FormPage.jsx
│           ├── ResultsPage.jsx
│           ├── FindShopPage.jsx
│           └── UserPage.jsx
├── alembic/                 # Database migrations
├── tests/                   # pytest test suite
├── .github/workflows/
│   └── deploy.yml           # CI/CD — deploys to GCP Cloud Run on push to main
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Getting Started

### Prerequisites
- Python 3.12+
- Docker Desktop (required — the database runs in a container)

### Local Setup

```bash
git clone https://github.com/Casazza24/SkiWare.git
cd SkiWare

# Copy env template (defaults work out of the box for local dev)
cp .env.example .env

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start the local postgres database
docker compose up postgres -d

# Run the backend (connects to local Docker postgres automatically)
python3 -m backend.main
```

App runs at `http://localhost:8080`.

### Local Setup with Docker (matches production exactly)

```bash
docker compose up --build
```

Frontend runs at `http://localhost:5173`.
Backend API runs at `http://localhost:8080`.
The `backend/` and `frontend/` directories are volume-mounted so changes reflect immediately in local development.

> **No GCP access needed for local dev.** The postgres service (`pgvector/pgvector:pg15`) runs entirely in Docker. Cloud SQL is only used in production.

### Running Tests

```bash
docker compose up postgres -d   # must be running first
pytest tests/ -v
```

The test suite connects to the local Docker postgres, applies the migration automatically on first run, and truncates the `users` table between each test. No manual setup needed.

---

## Connecting to Cloud SQL (GCP)

> **Only needed if you are running the `data_agent` ingestion pipeline against production or need direct DB access.** For normal backend development and testing, the local Docker postgres is sufficient.

### One-time setup

**1. Install tools:**
```bash
brew install postgresql
brew install cloud-sql-proxy
```

**2. Authenticate with GCP:**
```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project skiware
```

**3. Verify your account has been added as a Cloud SQL IAM user** — ask the project owner if you're not sure. They run:
```bash
gcloud sql users create YOUR_EMAIL --instance=skiware-db --type=CLOUD_IAM_USER
```

### Connecting via psql

**1. Start the Cloud SQL proxy in the background:**
```bash
cloud-sql-proxy skiware:us-central1:skiware-db --port 9470 &
```

**2. Connect using your IAM access token as the password:**
```bash
PGPASSWORD=$(gcloud auth print-access-token) psql "host=127.0.0.1 port=9470 dbname=skiware user=YOUR_EMAIL sslmode=disable"
```

Replace `YOUR_EMAIL` with your full email (e.g. `lako2765@colorado.edu` or `james@vallery.net`).

**3. When done, stop the proxy:**
```bash
kill %1
# or
lsof -ti:9470 | xargs kill -9
```

### Running data_agent against Cloud SQL

```bash
export CLOUD_SQL_INSTANCE="skiware:us-central1:skiware-db"
export DB_NAME="skiware"
export DB_USER="YOUR_EMAIL@colorado.edu"
export GCP_PROJECT="skiware"
export GCP_REGION="us-central1"

pip install -r data_agent/requirements.txt
python -m data_agent
```

No proxy needed for the data_agent — the Cloud SQL Python Connector authenticates via your Application Default Credentials automatically.

---

## Making Changes

### Workflow
1. Pull the latest `main`
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes under `backend/` or `frontend/`
4. Test locally
5. Open a PR against `main`

### Adding Python Dependencies

Add the package + pinned version to `requirements.txt`, then reinstall:

```bash
pip install <package>
pip freeze | grep <package>   # get the pinned version
# add it to requirements.txt manually
pip install -r requirements.txt
```

### Deployment

GitHub Actions now does two things:
1. Runs CI on every PR to `main`
2. Runs the same CI checks on `main` pushes, then deploys only if they pass

CI currently validates:
1. Python dependencies install cleanly
2. The FastAPI placeholder passes smoke tests
3. The Docker image builds successfully

Deployment on `main` then:
1. Builds a Docker image
2. Pushes it to GCP Artifact Registry
3. Deploys to GCP Cloud Run

**Do not merge to `main` unless the app runs locally.** There is no staging environment — `main` is production.

---

## Tech Stack

| Layer | Current | Target |
|---|---|---|
| Backend | Python / FastAPI | Python / FastAPI |
| Frontend | React / Vite | React |
| Server | Uvicorn | Uvicorn (FastAPI's async server) |
| Container | Docker | Docker |
| LLM | — | Gemini API (Google) |
| Vector Database | — | pgvector on GCP Cloud SQL (PostgreSQL) |
| Data Collection | — | GCP Cloud Run Jobs (scheduled Python agent) |
| Hosting | GCP Cloud Run | GCP Cloud Run |
| Container Registry | GCP Artifact Registry | GCP Artifact Registry |
| CI/CD | GitHub Actions | GitHub Actions |

### Current Backend

The service provides:

1. `POST /api/assess` — RAG-backed assessment via Gemini + pgvector retrieval
2. `GET /api/shops/nearest?lat=&lon=&ranked=` — Google Places API shop search with haversine distance, Google ratings, and review counts. `ranked=true` returns the top 5 shops scored by a Bayesian-adjusted rating + proximity formula; `ranked=false` (default) returns all results sorted by distance ascending.
3. `PUT/GET/DELETE /api/users/:id` — user CRUD with DIN calculation
4. `POST /api/auth/login` — email/password authentication

---

## Roadmap / Next Steps

### High priority

**1. Expand the RAG knowledge base**

The `data_agent` pipeline has only ingested 12 chunks (4 static docs). To improve assessment quality:
- Set `YOUTUBE_API_KEY` in the environment and populate `YouTubeSource.VIDEO_IDS` with real ski repair video IDs (evo, Sidecut Tuning, Peter Glenn channels are good sources)
- Fix or replace the web scraper sources — REI and evo block bots; swap for scraper-friendly alternatives or add proper `User-Agent` headers
- Re-run `python -m data_agent` against production Cloud SQL after adding sources

**2. End-to-end production test**

Run a full assess request against the live Cloud Run deployment with `GEMINI_API_KEY` set and Cloud SQL populated. Verify the RAG path returns non-empty `repairSteps` and `partsList`.

### Lower priority

**3. Ski value estimator**

Add an estimate of the gear's resale value alongside the repair cost so users can decide whether a repair is worth it.

**4. Condition report PDF export**

Shareable summary of the assessment result — useful for buying/selling used gear.

---

## Environment Variables

See `.env.example` for the full reference. Key variables:

| Variable | Local dev | Cloud Run (production) |
|---|---|---|
| `DB_HOST` | `localhost` (or `postgres` in docker-compose) | not set |
| `DB_NAME` | `skiware` | `skiware` |
| `DB_USER` | `skiware` | `skiware-app@skiware.iam.gserviceaccount.com` |
| `DB_PASSWORD` | `skiware` | not set (triggers IAM auth) |
| `CLOUD_SQL_INSTANCE` | not set | `skiware:us-central1:skiware-db` |
| `PORT` | `8080` | `8080` |
| `GCP_PROJECT` | `skiware` (data_agent only) | `skiware` |

Any secrets should be added as GitHub Actions secrets and passed to Cloud Run via `--set-env-vars` in the deploy step — never committed to the repo.

---

## PR Guidelines

- Keep PRs focused — one feature or fix per PR
- Test locally before opening a PR
- PRs require at least one approval before merging to `main`
- Merging to `main` = deploying to production
