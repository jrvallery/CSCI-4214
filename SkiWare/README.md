# SkiWare

An AI-powered ski and snowboard damage assessment and maintenance web app. Users describe their gear and any issues; SkiWare returns safety flags, severity ratings, DIY repair instructions, estimated shop costs, parts checklists, YouTube guides, and nearby shop locations — all powered by a RAG pipeline over a ski-specific knowledge base.

---

## Problem Statement

Ski repairs are expensive and intimidating for casual skiers. Most people can't distinguish between minor cosmetic damage and serious structural issues, leading to either unnecessary shop visits or dangerous equipment failures. Simple repairs that could be done at home often result in $50+ shop charges.

---

## Solution

A free web application where users input their ski info and describe their issue. SkiWare queries a knowledge base of ski-specific data to return:

- **Safety flag** — is it safe to ski on right now?
- **Severity indicator** — 1–5 scale with a clear DIY vs. take-to-a-shop verdict
- **Estimated shop cost** — so users know what they'd save by doing it themselves
- **Time and skill estimate** — how long it takes and what skill level is required
- **Step-by-step DIY repair instructions**
- **Parts checklist** — specific products with purchase links (Amazon, REI, evo)
- **Relevant YouTube repair guides**

---

## How It Works

1. **User fills out a modal** with their ski details:
   - Brand, model, year
   - Length
   - New/used condition
   - Last wax / edge sharpening (rough date)
   - Description of the issue

2. **RAG query** — the input searches a vector database of ski-specific knowledge (common issues by model, manufacturer specs, repair guides, parts sources)


3. **LLM response** — the Gemini API generates structured repair guidance grounded in the retrieved context with YouTube Links and purchase recommendations.

---

## Target Users

- **Primary:** Recreational skiers who want to save money and learn basic maintenance
- **Secondary:** Ski shops looking for quick damage assessment and quote generation

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python / FastAPI |
| Frontend | React / Vite |
| LLM | Gemini API (Google) |
| Vector Database | pgvector on GCP Cloud SQL (PostgreSQL) |
| Data Collection | GCP Cloud Run Jobs (scheduled Python agent) |
| Shop Search | Google Places API (New) |
| Hosting | GCP Cloud Run |
| Container Registry | GCP Artifact Registry |
| CI/CD | GitHub Actions |

> **Note:** The backend runs on FastAPI and the React frontend runs through Vite in local Docker development. See [CONTRIBUTING.md](CONTRIBUTING.md) for the current workflow.

---

## Architecture

```
User Browser
     │
     ▼
React Frontend          ← current local UI
     │ JSON over HTTP
     ▼
FastAPI Backend         ← current placeholder
     │
     ├── POST /api/assess
     │     ├── Embed user input
     │     ├── Query pgvector (retrieve relevant ski/repair context)
     │     └── Gemini API (LLM generates response with context)
     │     └── Gemini API (LLM generates structured response with context)
     │
     └── GET / (health, static)

Cloud Run Job (scheduled)
     │
     └── Data collection agent
           ├── Scrapes ski specs, common issues, repair guides, parts sources
           ├── Embeds and upserts into pgvector
           └── Creates GitHub issues for gaps / new data needs

Cloud SQL (PostgreSQL + pgvector)
     └── Stores ski knowledge base as vector embeddings
```

---

## Features

### Shipped
| Feature | Description |
|---|---|
| Assessment form | Equipment type, brand, length, age, snow type, terrain, maintenance history |
| Safety flag | Prominent yes/no — is it safe to ski on? |
| Severity indicator | 1–5 scale (color-coded) with DIY vs. shop verdict |
| Estimated shop cost | Dollar range of what a shop would charge for the same repair |
| Time + skill estimate | How long the repair takes and beginner / intermediate / advanced rating |
| Repair instructions | Step-by-step DIY guide |
| Parts checklist | Specific products with links to Amazon, REI, evo, Backcountry, Peter Glenn |
| YouTube guides | Relevant repair video search links |
| Nearby shops on results | Auto-detects location after assessment; shows top 5 shops ranked by rating + proximity |
| Find a Shop page | Full shop browser sorted by distance; shows all results with ratings and review counts |
| Google Places ratings | Shop cards show star rating and review count from Google Places API |
| User accounts | Sign up, log in, profile with equipment list and rider preferences |
| Dynamic assessment form | Pre-fills from user profile (equipment, skill level, terrain preference) |
| Auth button routing | Sign In / Create Account buttons route directly to the correct form view |

### Planned
| Feature | Description |
|---|---|
| Automated knowledge base | Cloud Run Job scrapes and embeds ski data on a schedule |
| Ski value estimator | "Your ski is worth ~$X used — a $Y repair may not be worth it" |
| Maintenance calendar | Wax/sharpen reminders based on ski type and usage |
| Condition report | Shareable PDF summary (useful for buying/selling used skis) |
| Photo upload | Vision model classifies damage type from a photo |
| Community repair logs | "47 people fixed this on a Rossignol Experience 88 — here's what worked" |
| Ski shop dashboard | Shop-facing version for quote generation and work orders |

---

## Key Technical Challenges

- **RAG quality** — response quality depends on knowledge base breadth. The data collection agent needs to cover a wide range of ski models and damage types.
- **Retrieval relevance** — embedding ski model + issue description well enough to retrieve the right context chunks
- **Structured output** — getting the LLM to return consistent severity scores, cost estimates, and skill levels across different inputs
- **Data sourcing** — finding reliable sources for ski specs, common issues, and repair guides to feed the agent

---

## Roadmap

### MVP
- [x] Migrate backend from Flask → FastAPI
- [x] Build React / Vite frontend
- [x] Gemini API integration with structured response (safety flag, severity, cost estimate, time/skill, instructions, parts, YouTube links)
- [x] RAG pipeline with pgvector
- [x] Initial knowledge base seeded manually
- [x] User accounts with equipment profiles
- [x] Dynamic assessment form pre-filled from user profile
- [x] Shop locator — Google Places API with haversine distance
- [x] Google Places ratings and review counts on shop cards
- [x] Nearby shops section on assessment results page (top-5 Bayesian ranking)

### v1
- [ ] Expand RAG knowledge base via Cloud Run data collection job
- [ ] Ski value estimator
- [ ] Maintenance calendar / wax reminders
- [ ] Condition report PDF export

### v2
- [ ] Vision model for photo-based damage classification
- [ ] Community repair logs
- [ ] Ski shop dashboard for quote generation

---

## Success Metrics

- Users get accurate repair guidance for common damage types (edge damage, base gouges, delamination)
- Severity and cost estimates align with real shop quotes
- Response includes at least one relevant YouTube guide and one purchase link
- Users report saving money vs. taking skis to a shop

---

## Contributing


See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup, branching workflow, and PR guidelines.

---

## Front-End Figma Mockup

https://www.figma.com/make/KqC5Oz8NcWsw9GHjK1UY6Z/-?t=HvXVJCTIa0UEwSLV-1&preview-route=%2Fassessment
