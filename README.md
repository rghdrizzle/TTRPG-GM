# TTRPG AI Game Master

A RAG-powered AI Game Master for tabletop RPGs. Players pick a pre-loaded rulebook,
start a campaign, and chat with an AI that knows the rules, remembers the story,
and can host multiple players in a shared room.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         BROWSER                                  │
│                    localhost:5173                                 │
│                                                                  │
│   ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌─────────────┐  │
│   │  /login  │  │/register │  │/dashboard │  │ /rulebooks  │  │
│   └──────────┘  └──────────┘  └───────────┘  └─────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP / fetch
                         │ Bearer token
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI                                     │
│                    localhost:8000                                 │
│                                                                  │
│   POST /auth/register     POST /auth/login                      │
│   JWT middleware          pydantic validation                    │
└──────────┬──────────────────────────┬───────────────────────────┘
           │                          │
           ▼                          ▼
┌──────────────────┐      ┌───────────────────────┐
│   POSTGRESQL     │      │       REDIS            │
│   localhost:5432 │      │    localhost:6379       │
│                  │      │                        │
│  ┌────────────┐  │      │   — rooms               │
│  │   users    │  │      │                        │
│  ├────────────┤  │      └───────────────────────┘
│  │ documents  │  │
│  ├────────────┤  │
│  │   chunks   │  │
│  │ +pgvector  │  │
│  └────────────┘  │
└──────────────────┘
```

---

## RAG Pipeline

```
                        INGEST (one time)
                        ────────────────
  fist.pdf
      │
      ▼
  PyPDFLoader          loads PDF pages as Documents
      │
      ▼
  RecursiveCharacter   splits into ~512 token chunks
  TextSplitter         with 64 token overlap
      │
      ▼
  CohereEmbeddings     converts each chunk to
  embed-english-v3.0   1024-dimension vector
      │
      ▼
  PostgreSQL           stores content + vector
  chunks table         in pgvector column


                        QUERY (every message)
                        ─────────────────────
  player message
      │
      ▼
  CohereEmbeddings     embed the question
      │
      ▼
  pgvector             cosine similarity search
  similarity search    returns top 5 chunks
      │
      ▼
  Claude Sonnet        GM prompt + RAG chunks
                       + session history
      │
      ▼
  SSE stream           response streamed back
                       to the browser
```

---

## Database Schema

```
┌─────────────────────────────────┐
│             users               │
├──────────┬──────────────────────┤
│ id       │ String (UUID)  PK    │
│ username │ String               │
│ email    │ String  UNIQUE       │
│ password │ String  (bcrypt)     │
│ created  │ DateTime             │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│           documents             │
├──────────┬──────────────────────┤
│ id       │ String (UUID)  PK    │
│ title    │ String               │  e.g. "FIST"
│ system   │ String               │  e.g. "FIST TTRPG"
│ file_path│ String  UNIQUE       │
│ created  │ DateTime             │
└─────────────────────────────────┘
          │
          │ 1 document → many chunks
          ▼
┌─────────────────────────────────┐
│             chunks              │
├──────────┬──────────────────────┤
│ id       │ String (UUID)  PK    │
│ doc_id   │ String  FK           │
│ content  │ Text                 │
│ section  │ String  (page no.)   │
│ embedding│ Vector(1024)         │  ← pgvector
│ created  │ DateTime             │
└─────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| API server | FastAPI + Python 3.13 | async, typed, auto docs |
| Server | Uvicorn | ASGI server that runs FastAPI |
| ORM | SQLAlchemy | most widely used Python ORM |
| DB driver | psycopg2 | Postgres driver |
| Database | PostgreSQL 17 + pgvector | one DB for everything including vectors |
| Migrations | Alembic | schema version control |
| Embeddings | Cohere embed-english-v3.0 | free tier, 1024 dims |
| LLM | Claude Sonnet (planned) | GM narration |
| Background | Celery + Redis (planned) | entity extraction, summaries |
| Frontend | SvelteKit + Tailwind | lighter than Next.js, no Turbopack issues |
| Auth | JWT + python-jose | stateless token auth |
| Package mgr | Poetry | virtualenv + dependency management |
| Containers | Docker Compose | local Postgres + Redis |

---

## Pages Built

```
/login          ← JWT auth, calls POST /auth/login
/register       ← calls POST /auth/register
/dashboard      ← lists campaigns (protected)
/rulebooks      ← shows loaded rulebooks (protected)
/unauthorized   ← shown when no token found
```

All pages follow the same industrial brutalist design system:
- Monochrome black + white
- Bebas Neue display font + Share Tech Mono
- Fake browser chrome + ruler at top
- Scrolling ticker + barcode strip at bottom
- Chinese subtitle text for flavor

---

## Auth Flow

```
Register:
  form → POST /register (username, email, password)
       → FastAPI hashes password with bcrypt
       → inserts user into DB
       → returns 200 OK
       → frontend redirects to /login

Login:
  form → POST /login (email, password)
       → FastAPI verifies password
       → returns { status: 200, payload: { token: "..." } }
       → frontend stores token in localStorage
       → redirects to /dashboard

Protected page:
  onMount → requireAuth() checks localStorage
          → no token → redirect to /unauthorized
          → token found → fetch data with Bearer header
```

---

## Token Helper — `src/lib/auth.ts`

```ts
setToken(token)    // stores JWT in localStorage
getToken()         // reads JWT from localStorage
requireAuth()      // redirects to /unauthorized if no token
logout()           // clears token + redirects to /login
```

---

## Ingest Script — `scripts/ingest.py`

```
Run once to load a rulebook into pgvector:

  poetry run python src/app/scripts/ingest.py

Steps:
  1. Check if document already ingested (skip if yes)
  2. Insert document row into documents table
  3. Load PDF with PyPDFLoader
  4. Split into chunks with RecursiveCharacterTextSplitter
     chunk_size=512, overlap=64
  5. For each chunk:
     a. Embed with Cohere (1024 dims)
     b. Insert into chunks table
     c. Sleep 0.7s (Cohere free tier = 100 calls/min)
  6. Commit every 50 chunks
```

---

## Environment Variables

### Backend — `app/.env`

```bash
# Database
POSTGRES_PASSWORD=yourpassword
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/postgres

# Redis
REDIS_PASS=yourredispassword
REDIS_URL=redis://:yourredispassword@localhost:6379

# Auth
SECRET_KEY=yoursecretkey
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI
COHERE_API_KEY=your-cohere-key
ANTHROPIC_API_KEY=(planned)

# App
DEBUG=True
```

### Frontend — `web/.env`

```bash
VITE_API_URL=http://localhost:8000
```

---

## Running the Project

```bash
# 1 — start database and redis
docker compose up -d

# 2 — run migrations
cd app
poetry run alembic upgrade head

# 3 — ingest rulebook (one time)
poetry run python src/app/scripts/ingest.py

# 4 — start backend
poetry run uvicorn app.main:app --reload

# 5 — start frontend (separate terminal)
cd web
npm run dev
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

---

## Progress

```
MONTH 1 — FOUNDATION
  ✓ Week 1 — FastAPI + auth + Docker + DB
  ✓ Week 2 — SvelteKit frontend + auth pages + dashboard
  ░ Week 3 — RAG pipeline (IN PROGRESS)
  ░ Week 4 — LLM + chat UI

MONTH 2 — MEMORY
  ░ Week 5 — Campaign + session persistence
  ░ Week 6 — Rolling summary memory
  ░ Week 7 — Entity extraction
  ░ Week 8 — Campaign dashboard

MONTH 3 — MULTIPLAYER
  ░ Week 9  — WebSocket rooms
  ░ Week 10 — Multiplayer UI
  ░ Week 11 — Polish + Discord bot (stretch)
  ░ Week 12 — Deploy + beta launch
```

---

## Useful Links

- [FastAPI docs](https://fastapi.tiangolo.com)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)
- [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [Cohere embeddings](https://docs.cohere.com/docs/embeddings)
- [LangChain text splitters](https://python.langchain.com/docs/concepts/text_splitters/)
- [SvelteKit docs](https://svelte.dev/docs/kit/introduction)
- [Anthropic API](https://docs.anthropic.com/en/api/getting-started)
- [Poetry docs](https://python-poetry.org/docs/)

