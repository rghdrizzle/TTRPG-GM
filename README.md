# TTRPG AI Game Master

A RAG-powered AI Game Master for tabletop RPGs. Players pick a pre-loaded rulebook,
start a campaign, and chat with an AI that knows the rules, remembers the story,
and can host multiple players in a shared room.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              BROWSER                                     │
│                          localhost:5173                                  │
│                                                                          │
│  /login  /register  /dashboard  /rulebooks  /unauthorized                │
│  /campaigns/new                                                          │
│  /campaigns/[id]/character/create                                        │
│  /campaigns/[id]/sessions                                                │
│  /campaigns/[id]/sessions/[session_id]/chat                              │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │ HTTP fetch + SSE stream
                            │ Bearer JWT token
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            FASTAPI                                       │
│                         localhost:8000                                   │
│                                                                          │
│  POST /auth/register       POST /auth/login                             │
│  POST /campaigns/new       GET  /campaigns                              │
│  GET  /campaigns/:id/sessions                                           │
│  POST /campaigns/:id/sessions/new                                       │
│  POST /campaigns/:id/characters                                         │
│  POST /:session_id/chat          ← SSE stream (agent pipeline)          │
│  GET  /:session_id/chat/history  ← load past turns                      │
│                                                                          │
│  JWT middleware · pydantic validation · CORS                            │
└──────────┬────────────────────────────┬────────────────────────────────┘
           │                            │
           ▼                            ▼
┌──────────────────────┐    ┌──────────────────────┐
│     POSTGRESQL       │    │        REDIS          │
│    localhost:5432    │    │    localhost:6379      │
│                      │    │                       │
│  users               │    │  (month 3 — rooms     │
│  documents           │    │   + celery broker)    │
│  chunks + pgvector   │    └──────────────────────┘
│  campaigns           │
│  sessions            │
│  turns               │
│  characters          │
│  entities            |
|   rooms              │
└──────────────────────┘
```

---

## Agent Pipeline (Chat Endpoint)

```
Player message
      │
      ▼
┌─────────────────────┐
│  INTENT CLASSIFIER  │  fast LLM call (llama3.1:8b)
│  classifier.py      │  returns Intent dataclass:
│                     │  - intent type (one of 6)
│                     │  - topics list for RAG
│                     │  - roll_needed / roll_provided
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   TOOL_MAP lookup   │  picks tools based on intent
│   tools.py          │
│                     │
│  rules_question     →  fetch_rag
│  lore_question      →  fetch_rag
│  world_question     →  fetch_rag
│  story_action       →  fetch_rag + fetch_history + fetch_world_state
│  action_with_roll   →  fetch_rag + fetch_character + fetch_history + fetch_roll
│  character_query    →  fetch_character
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   TOOLS EXECUTE     │  each tool returns a context string
│                     │
│  fetch_rag          →  hybrid search (dense + BM25) + rerank → top 8 chunks
│  fetch_character    →  reads characters table
│  fetch_history      →  reads turns table (last 12)
│  fetch_world_state  →  reads entities table
│  fetch_roll         →  parses dice notation, rolls, returns result
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  PROMPT_MAP lookup  │  picks template based on intent
│  gm.py              │  fills template with tool results
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   GM NARRATOR       │  Ollama nous-hermes2pro (streaming)
│                     │  SSE tokens → browser
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  SAVE TURN          │  save player_msg + gm_response to turns table
│  CHECK SUMMARY      │  if turns % 20 == 0 → trigger summary (Celery)
└─────────────────────┘
```

---

## RAG Pipeline

```
                    INGEST (one-time script)
                    ─────────────────────────
  fist.pdf
      │
      ▼
  PyPDFLoader              loads PDF pages as Documents
      │
      ▼
  RecursiveCharacter       splits into ~512 token chunks
  TextSplitter             with 64 token overlap
      │
      ▼
  OllamaEmbeddings         converts each chunk to
  nomic-embed-text         768-dimension vector (local, free)
      │
      ▼
  PostgreSQL               stores content + vector
  chunks table             in pgvector column


                    QUERY (every player message)
                    ──────────────────────────────
  topics list (from classifier)
      │
      ├── for each topic:
      │     dense search  → pgvector cosine similarity → top 5
      │     sparse search → BM25 in-memory keyword search → top 5
      │
      ▼
  merge + deduplicate by chunk id
      │
      ▼( This step is missing )
  CrossEncoder reranker    scores (query, chunk) pairs
  ms-marco-MiniLM-L-6-v2  returns relevance scores
      │
      ▼
  top 8 chunks             joined into context string
      │
      ▼
  injected into GM prompt
```

---

## Database Schema ( needs an update )

```
┌──────────────────────────────────┐
│              users               │
├───────────┬──────────────────────┤
│ id        │ String (UUID)  PK    │
│ username  │ String               │
│ email     │ String  UNIQUE       │
│ password  │ String  (bcrypt)     │
│ created_at│ DateTime             │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│            documents             │
├───────────┬──────────────────────┤
│ id        │ String (UUID)  PK    │
│ title     │ String               │
│ system    │ String               │
│ file_path │ String  UNIQUE       │
│ created_at│ DateTime             │
└──────────────────────────────────┘
           │
           │ 1 → many
           ▼
┌──────────────────────────────────┐
│              chunks              │
├───────────┬──────────────────────┤
│ id        │ String (UUID)  PK    │
│ document_id│ String  FK          │
│ content   │ Text                 │
│ section   │ String               │
│ embedding │ Vector(768)          │
│ created_at│ DateTime             │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│            campaigns             │
├───────────┬──────────────────────┤
│ id        │ String (UUID)  PK    │
│ name      │ String               │
│ rulebook  │ String               │
│ description│ Text                │
│ max_players│ Integer             │
│ summary   │ Text                 │  ← rolling compressed history
│ created_at│ DateTime             │
└──────────────────────────────────┘
           │
           │ 1 → many
           ▼
┌──────────────────────────────────┐
│             sessions             │
├───────────┬──────────────────────┤
│ id        │ String (UUID)  PK    │
│ campaign_id│ String  FK          │
│ name      │ String               │
│ status    │ String               │
│ created_at│ DateTime             │
└──────────────────────────────────┘
           │
           │ 1 → many
           ▼
┌──────────────────────────────────┐
│               turns              │
├───────────┬──────────────────────┤
│ id        │ String (UUID)  PK    │
│ session_id│ String  FK           │
│ player_msg│ Text                 │
│ gm_response│ Text                │
│ created_at│ DateTime             │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│            characters            │
├───────────┬──────────────────────┤
│ id        │ String (UUID)  PK    │
│ campaign_id│ String  FK          │
│ user_id   │ String  FK           │
│ name      │ String               │
│ class     │ String               │
│ level     │ Integer              │
│ hp        │ Integer              │
│ max_hp    │ Integer              │
│ stats     │ JSON                 │  e.g. {"METAL":4,"WIRE":2,"HEART":3}
│ inventory │ JSON                 │  [{name, qty}]
│ traits    │ JSON                 │  ["Tough", "Quick"]
│ notes     │ Text                 │
│ created_at│ DateTime             │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│             entities             │
├───────────┬──────────────────────┤
│ id        │ String (UUID)  PK    │
│ campaign_id│ String  FK          │
│ name      │ String               │
│ type      │ String               │  NPC/location/item/faction
│ description│ Text                │
│ created_at│ DateTime             │
└──────────────────────────────────┘
```

---

## Services Structure ( needs an update )

```
services/
├── rag.py          ← embedding + hybrid search (dense + BM25) + reranking
├── gm.py           ← PROMPT_MAP + 6 prompt templates + stream_gm_response
├── classifier.py   ← classify(message) → Intent dataclass
└── tools.py        ← TOOL_MAP + fetch_rag, fetch_character,
                       fetch_history, fetch_world_state, fetch_roll
```

---

## Intent Types + Tool Map

| Intent | RAG | Character | History | World State | Roll |
|---|---|---|---|---|---|
| rules_question | ✓ | | | | |
| lore_question | ✓ | | | | |
| world_question_from_rulebook | ✓ | | | | |
| story_action | ✓ | | ✓ | ✓ | |
| action_with_dice_roll | ✓ | ✓ | ✓ | | ✓ |
| character_query | | ✓ | | | |

---

## Rolling Summary

```
Every 20 turns:
  → fetch turns 1-20 (oldest unsummarised batch)
  → call LLM with compression prompt
  → preserves: NPC names, locations, player decisions, plot threads
  → discards: individual rolls, repeated attempts, small talk
  → append result to campaigns.summary
  → turns stay in DB forever (never deleted)

GM prompt always contains:
  <campaign_summary>  compressed history of everything before window
  <recent_turns>      last 12 turns verbatim
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| API server | FastAPI + Python 3.13 | async, typed, auto docs |
| Server | Uvicorn | ASGI server that runs FastAPI |
| ORM | SQLAlchemy | most widely used Python ORM |
| DB driver | psycopg2 | Postgres driver for SQLAlchemy |
| Database | PostgreSQL 17 + pgvector | one DB for everything |
| Migrations | Alembic | schema version control |
| Embeddings | nomic-embed-text via Ollama | free, local, 768 dims |
| Sparse search | BM25 (rank-bm25 / LlamaIndex) | keyword search over chunks |
| Reranker | CrossEncoder ms-marco-MiniLM | scores (query, chunk) relevance |
| PDF parsing | PyPDFLoader + LangChain | loads and splits rulebook PDFs |
| LLM (GM) | nous-hermes2pro via Ollama | better tool following than llama3 |
| LLM (classifier) | llama3.1:8b via Ollama | fast intent classification |
| SSE streaming | sse-starlette | streams LLM tokens to browser |
| Frontend | SvelteKit + Tailwind | lighter than Next.js |
| Auth | JWT + python-jose | stateless token auth |
| Package mgr | Poetry | virtualenv + dependency management |
| Containers | Docker Compose | local Postgres + Redis |
| Background | Celery + Redis | session summaries (planned) |

---

## Project Structure ( needs updating )

```
TTRPG-GM/
├── app/
│   ├── pyproject.toml
│   ├── docker-compose.yml
│   ├── .env
│   ├── alembic/
│   └── src/app/
│       ├── main.py
│       ├── config.py
│       ├── db/db.py
│       ├── models/
│       │   ├── user.py
│       │   ├── document.py
│       │   ├── chunk.py
│       │   ├── campaign.py
│       │   ├── session.py
│       │   ├── turn.py
│       │   ├── character.py
│       │   └── entity.py
│       ├── routers/
│       │   ├── auth.py
│       │   └── routes.py
│       ├── services/
│       │   ├── rag.py
│       │   ├── gm.py
│       │   ├── classifier.py
│       │   └── tools.py
│       ├── pdfs/fist.pdf
│       └── scripts/ingest.py
│
└── web/
    ├── .env
    └── src/
        ├── lib/auth.ts
        └── routes/
            ├── login/+page.svelte
            ├── register/+page.svelte
            ├── dashboard/+page.svelte
            ├── rulebooks/+page.svelte
            ├── unauthorized/+page.svelte
            └── campaigns/
                ├── new/+page.svelte
                └── [id]/
                    ├── character/create/+page.svelte
                    └── sessions/
                        ├── +page.svelte
                        └── [session_id]/chat/+page.svelte
```

---

## Pages Built ( needs updating )

```
/login                                          ← JWT auth
/register                                       ← account creation
/dashboard                                      ← campaign list
/rulebooks                                      ← FIST rulebook hardcoded
/unauthorized                                   ← no token redirect
/campaigns/new                                  ← 3-phase campaign creation
/campaigns/[id]/character/create               ← 5-phase character creation + dice
/campaigns/[id]/sessions                        ← session list + create session
/campaigns/[id]/sessions/[session_id]/chat     ← GM chat + SSE stream + history
```

Design system — all pages:
- Monochrome black + white
- Bebas Neue display + Share Tech Mono
- Fake browser chrome + ruler at top
- Scrolling ticker + barcode at bottom
- Chinese subtitle text

---

## Auth Flow

```
Register → POST /register (username, email, password)
         → bcrypt hash → insert user → 200 OK → redirect /login

Login    → POST /login (email, password)
         → verify hash → { status:200, payload: { token } }
         → localStorage.setItem("token") → redirect /dashboard

Protected page → onMount → requireAuth()
               → no token → /unauthorized
               → token found → Bearer header on every fetch
```

---

## Running the Project

```bash
# 1 — start Postgres + Redis
docker compose up -d

# 2 — run migrations
cd app
poetry run alembic upgrade head

# 3 — start Ollama
ollama serve
ollama pull nomic-embed-text
ollama pull nous-hermes2pro
ollama pull llama3.1:8b

# 4 — ingest rulebook (one time)
poetry run python src/app/scripts/ingest.py

# 5 — start backend
poetry run uvicorn src.app.main:app --reload

# 6 — start frontend
cd web && npm run dev
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| Ollama | http://localhost:11434 |

---

## Progress

```
MONTH 1 — FOUNDATION
  ✓ Week 1 — FastAPI + auth + Docker + pgvector
  ✓ Week 2 — SvelteKit + all auth pages + dashboard
  ✓ Week 3 — RAG ingest script + pgvector search
  ✓ Week 4 — SSE chat + turns table + history reload

MONTH 2 — INTELLIGENCE
  ✓ Week 5 — Intent classifier + TOOL_MAP + PROMPT_MAP
              + hybrid RAG (BM25 + dense + reranking)
              + character creation page
  ░ Week 6 — Rolling summary (every 20 turns → campaigns.summary)
  ░ Week 7 — Entity extraction (Celery background tasks)
  ✓ Week 8 — Campaign dashboard with entity log

MONTH 3 — MULTIPLAYER
  ✓ Week 9  — WebSocket rooms + Redis pub/sub
  ░ Week 10 — Multiplayer UI
  ░ Week 11 — Polish + rate limiting
  ░ Week 12 — Deploy: Railway + Vercel
```

---

## Useful Links

| Topic | Link |
|---|---|
| FastAPI | https://fastapi.tiangolo.com |
| SQLAlchemy | https://docs.sqlalchemy.org/en/20/orm/quickstart.html |
| Alembic | https://alembic.sqlalchemy.org/en/latest/tutorial.html |
| pgvector | https://github.com/pgvector/pgvector |
| LlamaIndex BM25 | https://docs.llamaindex.ai/en/stable/examples/retrievers/bm25_retriever/ |
| CrossEncoder | https://www.sbert.net/docs/cross_encoder/usage/usage.html |
| ms-marco reranker | https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-6-v2 |
| Ollama | https://ollama.com |
| nous-hermes2pro | https://ollama.com/library/nous-hermes2pro |
| sse-starlette | https://github.com/sysid/sse-starlette |
| SvelteKit | https://svelte.dev/docs/kit/introduction |
| Anthropic API | https://docs.anthropic.com/en/api/getting-started |
| Poetry | https://python-poetry.org/docs/ |
| Pinecone RAG guide | https://www.pinecone.io/learn/series/rag/rerankers/ |

---

## .gitignore

```
.env
__pycache__/
.venv/
*.pyc
.DS_Store
node_modules/
.svelte-kit/
pdfs/
```