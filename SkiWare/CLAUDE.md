# SkiWare — Claude Code Guide

## Project Overview

SkiWare is an AI-powered ski/snowboard damage assessment and maintenance web app. Users describe their gear and any issues; the app returns safety flags, severity ratings, DIY repair instructions, shop cost estimates, parts checklists, and nearby shop locations.

**Stack:** Python/FastAPI backend · React/Vite frontend · Gemini API (LLM) · pgvector on GCP Cloud SQL · GCP Cloud Run

---

## Local Development

```bash
# Preferred: Docker (matches production)
docker compose up --build
# Frontend: http://localhost:5173
# Backend:  http://localhost:8080

# Alternative: run backend directly
source .venv/bin/activate
python3 -m backend.main
```

The `backend/` and `frontend/` directories are volume-mounted in Docker — changes hot-reload without rebuilding.

---

## Project Structure

```
SkiWare/
├── backend/
│   ├── main.py              # FastAPI app entrypoint — registers all routers
│   ├── routers/
│   │   ├── assessments.py   # POST /api/assess
│   │   ├── users.py         # User management endpoints
│   │   └── shops.py         # GET /api/shops/nearest?lat&lon&ranked
│   ├── services/
│   │   ├── assessment.py    # Assessment logic
│   │   ├── users.py         # User service logic
│   │   └── calculate_DIN.py # DIN binding calculation
│   └── models/
│       ├── assesment.py     # Assessment request/response models
│       ├── user.py          # User models
│       └── recommendation.py
├── frontend/
│   └── src/
│       ├── App.jsx          # Root: page state machine + routing
│       ├── App.css          # All styles (single stylesheet)
│       ├── components/
│       │   └── Header.jsx   # Sticky nav — add new nav items here
│       └── pages/
│           ├── HomePage.jsx
│           ├── FormPage.jsx
│           ├── ResultsPage.jsx   # includes NearbyShops component (auto-fetches, ranked=true)
│           ├── FindShopPage.jsx  # full shop browser (all results, sorted by distance)
│           └── UserPage.jsx
├── requirements.txt
├── docker-compose.yml
└── Dockerfile
```

---

## Units

All user-facing measurements use **imperial units**:

| Field | Unit | Notes |
|---|---|---|
| `weightLbs` | pounds (lbs) | Converted to kg internally before DIN calculation (`× 0.453592`) |
| `heightIn` | inches (in) | Stored as decimal inches (e.g. 69.0 = 5′9″); not used in DIN calc |
| `bootSoleLengthMm` | millimeters (mm) | Stays in mm — industry universal standard printed on every boot |
| `distance_miles` | miles (mi) | Shop search radius and distance display |

**Do not add metric fields.** If a new measurement is introduced, use imperial and convert to metric internally where needed (e.g. for external APIs or calculation tables that require SI units).

---

## Key Conventions

### Backend
- All routers use prefix `/api` and are registered in `backend/main.py`
- Pydantic models live in `backend/models/`, business logic in `backend/services/`
- `httpx` is available for async HTTP calls (already in `requirements.txt`)

#### Routers must be thin
Routers handle only HTTP concerns: parameter parsing, calling a service function, and mapping results to HTTP responses (status codes, error raises). All business logic — API calls, data transformations, calculations, validation — belongs in a service function.

**Correct pattern:**
```python
# routers/shops.py
@router.get("/shops/nearest")
async def nearest_shops(lat: float = Query(...), lon: float = Query(...), ranked: bool = Query(False)):
    return await find_nearest_shops(lat, lon, ranked=ranked)  # all logic lives in the service
```

**Wrong pattern:**
```python
# routers/shops.py  ← don't put logic here
@router.get("/shops/nearest")
async def nearest_shops(lat: float, lon: float):
    async with httpx.AsyncClient() as client:  # ← this belongs in services/
        resp = await client.post(...)
        ...
```

When adding a new endpoint, create or update a file in `backend/services/` first, then wire it up in the router with a one- or two-line handler.

#### Shop endpoint behaviour
`GET /api/shops/nearest` accepts an optional `ranked` boolean (default `false`):
- `ranked=false` — returns **all** results sorted by distance ascending. Used by `FindShopPage`.
- `ranked=true` — returns **top 5** results scored by Bayesian-adjusted rating + proximity (equal weights). Used by the `NearbyShops` component inside `ResultsPage`. The Bayesian prior is 3.5 stars at 25 reviews — shops with thin review counts are pulled toward the prior before scoring.

The response always includes `rating` (float | null) and `user_rating_count` (int | null) from the Google Places API.

### Frontend
- Navigation is a state machine in `App.jsx` — `currentPage` drives which page renders
- The `<Header>` is rendered once at the `App` level; individual pages must **not** render their own header
- All styles live in `App.css` — no separate component stylesheets
- Pages receive navigation callbacks as props (`onBackToHome`, `onFindShop`, etc.)
- `UserPage` accepts an `initialView` prop (`'login'` | `'create'` | `null`). The Header's Sign In button passes `'login'` and Create Account passes `'create'` via `handleNavigate` in `App.jsx`. Navigating to `'user'` directly leaves `initialView` null (defaults to profile if logged in, idle otherwise).

---

## Database

### Local development
PostgreSQL runs as a Docker service named `db`. `docker compose up --build` starts it automatically. The app connects via `DATABASE_URL=postgresql+asyncpg://skiware:skiware@db:5432/skiware`.

After first bringing the stack up, run migrations:
```bash
docker compose exec app alembic upgrade head
```

### Adding a migration
```bash
# Auto-generate from model changes
docker compose exec app alembic revision --autogenerate -m "describe the change"
# Then review alembic/versions/<id>_describe_the_change.py before committing
```

### ORM models
SQLAlchemy table definitions live in `backend/models/tables.py`. Pydantic request/response models stay in `backend/models/user.py` etc. — they are separate concerns.

`Base` (from `backend/database.py`) must be imported in `alembic/env.py` and any file that creates tables for testing, so SQLAlchemy knows about all tables.

### DB session in services
Inject `db: AsyncSession` into service functions. The router passes it via `Depends(get_db)`:
```python
# router
async def get_users(db: AsyncSession = Depends(get_db)):
    return await list_users(db)

# service
async def list_users(db: AsyncSession) -> UserListResponse:
    result = await db.execute(select(UserTable))
    ...
```

### GCP Cloud SQL
On Cloud Run, set `DATABASE_URL` to one of:
- **Cloud SQL Auth Proxy (recommended):** `postgresql+asyncpg://user:pass@localhost:5432/dbname` — the proxy runs as a sidecar and exposes Cloud SQL on localhost
- **Direct TCP (public IP):** `postgresql+asyncpg://user:pass@PUBLIC_IP/dbname`

The proxy approach is standard — no firewall rules needed, and credentials are handled by IAM.

### Testing
Tests use an in-memory SQLite database via `aiosqlite`. The `db_override` fixture in `tests/conftest.py` replaces the `get_db` dependency for every test automatically — no test touches the real Postgres instance.

---

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `PORT` | Port the backend listens on | No (default `8080`) |
| `DATABASE_URL` | Postgres connection string (`postgresql+asyncpg://...`) | Yes — set automatically in docker-compose |
| `GOOGLE_PLACES_API_KEY` | Google Places API key for `/api/shops/nearest` | Yes (for shop search) |
| `GEMINI_API_KEY` | Gemini API key for LLM assessment | Yes (in production) |

Never commit secrets — add them as GitHub Actions secrets and pass to Cloud Run via `--set-env-vars`.

---

## Adding a New API Endpoint

1. Create or update a file in `backend/routers/`
2. Define an `APIRouter` with `prefix="/api"`
3. Register it in `backend/main.py` with `app.include_router(...)`
4. Add corresponding Pydantic models to `backend/models/` if needed

## Adding a New Frontend Page

1. Create `frontend/src/pages/YourPage.jsx` — do **not** include `<Header>` inside it
2. Add a handler in `App.jsx` (e.g. `handleYourPage`) that sets `currentPage`
3. Render the page in `App.jsx`'s return block with `{currentPage === 'yourPage' && <YourPage ... />}`
4. Add a nav entry to `Header.jsx` if it should appear in the top nav

---

## Deployment

Push to `main` → GitHub Actions builds, pushes to GCP Artifact Registry, deploys to Cloud Run. There is no staging environment — **main is production**. Test locally before merging.
