# TTRPG AI Game Master

A RAG-powered AI Game Master for tabletop RPGs. Players pick a pre-loaded rulebook,
start a campaign, and chat with an AI that knows the rules, remembers the story,
and can host multiple players in a shared room.

---

## Architecture

```mermaid
flowchart TB
    subgraph Browser["BROWSER — localhost:5173"]
        direction TB
        B1["/login  /register  /dashboard  /rulebooks  /unauthorized"]
        B2["/campaigns/new"]
        B3["/campaigns/[id]/character/create"]
        B4["/campaigns/[id]/sessions"]
        B5["/campaigns/[id]/sessions/[session_id]/chat"]
        B6["/rooms/[room_id]/lobby"]
        B7["/rooms/[room_id]/game"]
    end

    subgraph API["FASTAPI — localhost:8000"]
        direction TB
        A1["POST /auth/register · POST /auth/login"]
        A2["POST /campaigns/new · GET /campaigns"]
        A3["GET /campaigns/:id/sessions"]
        A4["POST /campaigns/:id/sessions/new"]
        A5["POST /campaigns/:id/characters"]
        A6["POST /:session_id/chat  ← SSE stream (agent pipeline)"]
        A7["GET /:session_id/chat/history  ← load past turns"]
        A8["WS /ws/room/:room_id  ← multiplayer WebSocket"]
        A9["JWT middleware · pydantic validation · CORS"]
    end

    subgraph PG["POSTGRESQL — localhost:5432"]
        direction TB
        P1["users"]
        P2["documents"]
        P3["chunks + pgvector"]
        P4["campaigns"]
        P5["sessions"]
        P6["turns"]
        P7["characters"]
        P8["entities"]
        P9["rooms"]
    end

    subgraph RD["REDIS — localhost:6379"]
        direction TB
        R1["pub/sub per room"]
        R2["round buffer staging"]
        R3["celery broker"]
    end

    Browser -->|"HTTP fetch + SSE stream + WebSocket — Bearer JWT token"| API
    API --> PG
    API --> RD
```

---

## Agent Pipeline (Chat Endpoint)

```mermaid
flowchart TD
    Start(["Player message(s)<br/><i>multiplayer: all players' actions collected<br/>in round buffer, then flushed via /gm resolve</i>"])

    Start --> Classifier

    subgraph Classifier["INTENT CLASSIFIER — classifier.py"]
        C1["fast LLM call (llama3.1:8b)<br/>returns Intent dataclass:<br/>intent type (1 of 6) · topics list for RAG · roll_needed / roll_provided"]
    end

    Classifier --> ToolMap

    subgraph ToolMap["TOOL_MAP lookup — tools.py"]
        direction LR
        T1["rules_question → fetch_rag"]
        T2["lore_question → fetch_rag"]
        T3["world_question → fetch_rag"]
        T4["story_action → fetch_rag + fetch_history + fetch_world_state"]
        T5["action_with_roll → fetch_rag + fetch_character + fetch_history + fetch_roll"]
        T6["character_query → fetch_character"]
    end

    ToolMap --> Tools

    subgraph Tools["TOOLS EXECUTE"]
        direction LR
        TE1["fetch_rag → hybrid search (dense + BM25) + rerank → top 8 chunks"]
        TE2["fetch_character → reads characters table (all party members)"]
        TE3["fetch_history → reads turns table (last 12)"]
        TE4["fetch_world_state → reads entities table"]
        TE5["fetch_roll → parses dice notation, rolls, returns result"]
    end

    Tools --> Prompt

    subgraph Prompt["PROMPT_MAP lookup — gm.py"]
        PR1["picks template based on intent<br/>fills template with tool results<br/>includes party_context block for multiplayer sessions"]
    end

    Prompt --> Narrator

    subgraph Narrator["GM NARRATOR — hermes3 (Ollama)"]
        N1["extended thinking: internal reasoning pass first<br/>then narrative output<br/>SSE tokens → broadcast to all room WebSockets"]
    end

    Narrator --> Save

    subgraph Save["SAVE TURN"]
        S1["save player_msg + gm_response to turns table"]
        S2["if turns % 20 == 0 → trigger summary (Celery)"]
    end
```

---

## Multiplayer Round Buffer

```mermaid
flowchart TD
    PA["Player A sends action"] --> Buf
    PB["Player B sends action"] --> Buf
    PC["Player C sends action"] --> Buf

    Buf["Redis round buffer<br/>(keyed by room_id)"] --> Resolve

    Resolve["GM or host calls /gm resolve"] --> Combine

    Combine["Combined query assembled<br/>from all staged actions"] --> Pipeline

    Pipeline["Agent pipeline runs once<br/>with full party context"] --> Broadcast

    Broadcast["GM response streamed to all room WebSockets<br/>via Redis pub/sub broadcast"]
```

---

## RAG Pipeline

### Ingest (one-time script)

```mermaid
flowchart TD
    PDF["fist.pdf"] --> Loader["PyPDFLoader<br/>loads PDF pages as Documents"]
    Loader --> Splitter["RecursiveCharacterTextSplitter<br/>splits into ~512 token chunks, 64 token overlap"]
    Splitter --> Embed["OllamaEmbeddings — nomic-embed-text<br/>converts each chunk to 768-dim vector (local, free)"]
    Embed --> Store["PostgreSQL chunks table<br/>stores content + vector in pgvector column"]
```

### Query (every player message)

```mermaid
flowchart TD
    Topics["topics list (from classifier)"] --> Dense
    Topics --> Sparse

    Dense["dense search<br/>pgvector cosine similarity → top 5"] --> Merge
    Sparse["sparse search<br/>BM25 in-memory keyword search → top 5"] --> Merge

    Merge["merge + deduplicate by chunk id"] --> Rerank

    Rerank["CrossEncoder reranker — ms-marco-MiniLM-L-6-v2<br/>scores (query, chunk) pairs"] --> Top8

    Top8["top 8 chunks joined into context string"] --> Prompt["injected into GM prompt"]
```

---

## Database Schema

```mermaid
erDiagram
    documents ||--o{ chunks : "has"
    campaigns ||--o{ sessions : "has"
    campaigns ||--o{ characters : "has"
    campaigns ||--o{ entities : "has"
    sessions ||--o{ turns : "has"
    sessions ||--o{ rooms : "has"
    users ||--o{ characters : "owns"
    users ||--o{ rooms : "hosts"

    users {
        string id PK "UUID"
        string username
        string email UK
        string password "bcrypt"
        datetime created_at
    }

    documents {
        string id PK "UUID"
        string title
        string system
        string file_path UK
        datetime created_at
    }

    chunks {
        string id PK "UUID"
        string document_id FK
        text content
        string section
        vector embedding "768 dims"
        datetime created_at
    }

    campaigns {
        string id PK "UUID"
        string name
        string rulebook
        text description
        int max_players
        text summary "rolling compressed history"
        datetime created_at
    }

    sessions {
        string id PK "UUID"
        string campaign_id FK
        string name
        string status
        datetime created_at
    }

    turns {
        string id PK "UUID"
        string session_id FK
        text player_msg
        text gm_response
        datetime created_at
    }

    characters {
        string id PK "UUID"
        string campaign_id FK
        string user_id FK
        string name
        string class
        int level
        int hp
        int max_hp
        json stats "e.g. METAL:4, WIRE:2, HEART:3"
        json inventory "[{name, qty}]"
        json traits "[Tough, Quick]"
        text notes
        datetime created_at
    }

    entities {
        string id PK "UUID"
        string campaign_id FK
        string name
        string type "NPC/location/item/faction"
        text description
        datetime created_at
    }

    rooms {
        string id PK "UUID"
        string session_id FK
        string invite_code UK "short alphanumeric join code"
        string host_id FK
        string status "lobby/active/closed"
        datetime created_at
    }
```

---

## Redis-WebSocket Flow

```mermaid
flowchart TD
    Join["User joins room"] --> Auth

    Auth["extract JWT from query param (?token=...)<br/>verify + load user<br/>reject if invalid/expired<br/><i>not from oauth2_scheme — WS-safe dependency</i>"] --> Exists

    Exists{"room exists?"}
    Exists -->|"YES"| AcceptExisting["accept ws<br/>append to rooms[room_id]"]
    Exists -->|"NO — new room"| CreateRoom["rooms[room_id] = [socket]<br/>redis.subscribe(room_id)<br/>create_task(reader) — once per room"]

    CreateRoom --> Reader
    AcceptExisting --> Ready["room ready"]

    subgraph Reader["reader task (background, 1 per room)"]
        RLoop["loop:<br/>get_message()<br/>if msg: for socket in rooms[room_id]: send_text()<br/>sleep(0.01)"]
    end

    UserSend["User sends message"] --> Broadcast["broadcast(msg)"] --> Publish["redis.publish()"] --> Reader

    UserLeave["User leaves room"] --> Remove["remove from rooms[room_id]"]
    Remove --> LastCheck{"last user in room?"}
    LastCheck -->|"YES"| Cleanup["task.cancel()<br/>redis.unsubscribe"]
    LastCheck -->|"NO"| Done["done"]
```

**Notes:**
- 1 pubsub reader task per room, not per user
- reader lives until the last user leaves
- JWT extracted from query param, not Authorization header
- presence tracked via connect/disconnect events → broadcast to room

---

## Why Redis pub/sub — not direct broadcast

Without Redis, broadcasting means the sender's WebSocket handler loops over
every other connection and calls `send()` directly. This works, but only if all
connections live in the same server process.

```mermaid
flowchart TD
    subgraph Worker1_only["WITHOUT REDIS — single process only"]
        A1["user A (worker 1) sends message"] --> Loop["handler loops self.rooms[room_id]"]
        Loop --> SB["send to user B (worker 1) ✓"]
        Loop --> SC["send to user C (worker 1) ✓"]
        Loop -.-> SD["user D is on worker 2 — never reached ✗"]
    end
```

With Redis, any process publishes to a channel. Every process subscribed to
that channel receives it and fans out to its own local connections. Processes
don't need to know about each other.

```mermaid
flowchart TD
    subgraph MultiWorker["WITH REDIS — works across processes / machines"]
        UA["user A (worker 1) sends message"] --> Pub["redis.publish(room_id, msg)"]
        Pub --> W1["worker 1 subscriber receives it"]
        Pub --> W2["worker 2 subscriber receives it"]
        W1 --> SendBC["sends to user B, user C (local sockets)"]
        W2 --> SendD["sends to user D (local socket)"]
    end
```

For this project there is only one Uvicorn worker, so Redis is not strictly
required for correctness right now. It is used anyway because:

1. the round buffer (staged player actions) needs a shared store that
   survives across requests, which in-memory dicts cannot provide
2. Celery uses Redis as its task broker for background summarisation
3. when deploy time comes, scaling to multiple workers requires zero
   changes to the WebSocket code — Redis already handles it

---

## Services Structure

```
services/
├── rag.py          ← embedding + hybrid search (dense + BM25) + reranking
├── gm.py           ← PROMPT_MAP + 6 prompt templates + stream_gm_response
│                      party_context block injected for multiplayer sessions
├── classifier.py   ← classify(message) → Intent dataclass
└── tools.py        ← TOOL_MAP + fetch_rag, fetch_character (all party members),
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

```mermaid
flowchart TD
    Trigger["Every 20 turns"] --> Fetch["fetch turns 1-20 (oldest unsummarised batch)"]
    Fetch --> LLM["call LLM with compression prompt"]
    LLM --> Preserve["preserves: NPC names, locations,<br/>player decisions, plot threads"]
    LLM --> Discard["discards: individual rolls,<br/>repeated attempts, small talk"]
    Preserve --> Append["append result to campaigns.summary"]
    Discard --> Append
    Append --> Keep["turns stay in DB forever (never deleted)"]
```

GM prompt always contains:

| Block | Contents |
|---|---|
| `<party_context>` | all player characters in the room (multiplayer) |
| `<campaign_summary>` | compressed history of everything before window |
| `<recent_turns>` | last 12 turns verbatim |

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
| LLM (GM) | hermes3 via Ollama | extended thinking + narration |
| LLM (classifier) | llama3.1:8b via Ollama | fast intent classification |
| SSE streaming | sse-starlette | streams LLM tokens to browser |
| WebSocket | FastAPI WebSocket | multiplayer real-time comms |
| Pub/sub | Redis pub/sub | cross-room WebSocket broadcast |
| Frontend | SvelteKit + Tailwind | lighter than Next.js |
| Auth | JWT + python-jose | stateless token auth |
| WS Auth | query param token + custom dep | oauth2_scheme incompatible with WS |
| Package mgr | Poetry | virtualenv + dependency management |
| Containers | Docker Compose | local Postgres + Redis |
| Background | Celery + Redis | session summaries |

---

## Project Structure

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
│       │   ├── entity.py
│       │   └── room.py
│       ├── routers/
│       │   ├── auth.py
│       │   ├── routes.py
│       │   └── ws.py          ← WebSocket room endpoints
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
                        ├── [session_id]/chat/+page.svelte
                        └── [session_id]/rooms/
                            └── [room_id]/
                                ├── lobby/+page.svelte   ← invite code + ready state
                                └── game/+page.svelte    ← shared narration + action input
```

---

## Pages Built

```
/login                                                   ← JWT auth
/register                                                ← account creation
/dashboard                                               ← campaign list
/rulebooks                                               ← FIST rulebook hardcoded
/unauthorized                                            ← no token redirect
/campaigns/new                                           ← 3-phase campaign creation
/campaigns/[id]/character/create                        ← 5-phase character creation + dice
/campaigns/[id]/sessions                                 ← session list + create session
/campaigns/[id]/sessions/[session_id]/chat              ← GM chat + SSE stream + history
/campaigns/[id]/sessions/[session_id]/rooms/[room_id]/lobby  ← invite code + ready state
/campaigns/[id]/sessions/[session_id]/rooms/[room_id]/game   ← multiplayer game view
```

Design system — all pages:
- Monochrome black + white
- Bebas Neue display + Share Tech Mono
- Fake browser chrome + ruler at top
- Scrolling ticker + barcode at bottom
- Chinese subtitle text

---

## Multiplayer UI — Lobby Page

```
┌─────────────────────────────────────────────────────┐
│  ROOM LOBBY                                         │
│                                                     │
│  Invite Code: [ XKCD-42 ]  ← copy to clipboard     │
│                                                     │
│  Players                                            │
│  ● Jake (host)     [READY]                          │
│  ● Alex            [READY]                          │
│  ● Morgan          [waiting...]                     │
│                                                     │
│  ● = green dot presence indicator                   │
│                                                     │
│  [ START GAME ]  ← host only, all-ready gated       │
└─────────────────────────────────────────────────────┘
```

## Multiplayer UI — Game View

```
┌──────────────────────────────────────────────────────────────┐
│  ┌────────────────────────────┐  ┌────────────────────────┐  │
│  │   PARTY                   │  │   GM NARRATION         │  │
│  │                           │  │                        │  │
│  │  ● Jake                   │  │  [streaming GM text    │  │
│  │    Rook / Soldier         │  │   broadcast to all     │  │
│  │    HP: 12/14              │  │   players in room]     │  │
│  │                           │  │                        │  │
│  │  ● Alex                   │  └────────────────────────┘  │
│  │    Sable / Medic          │                              │
│  │    HP: 8/10               │  ┌────────────────────────┐  │
│  │                           │  │   YOUR ACTION          │  │
│  │  ○ Morgan  (disconnected) │  │                        │  │
│  │    Vex / Hacker           │  │  [ type your action ]  │  │
│  │    HP: 6/6                │  │  [ SUBMIT ]            │  │
│  │                           │  │                        │  │
│  └────────────────────────────┘  │  Staged: waiting for  │  │
│                                  │  other players...     │  │
│                                  └────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘

  ● = connected (green dot)
  ○ = disconnected (grey dot)
  action input disabled while GM is narrating
  all players see the same narration panel in real time
```

---

## Auth Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend

    U->>F: fill register form (username, email, password)
    F->>B: POST /register
    B->>B: bcrypt hash → insert user
    B-->>F: 200 OK
    F-->>U: redirect /login

    U->>F: fill login form (email, password)
    F->>B: POST /login
    B->>B: verify hash
    B-->>F: { status:200, payload: { token } }
    F->>F: localStorage.setItem("token")
    F-->>U: redirect /dashboard

    U->>F: visit protected page
    F->>F: onMount → requireAuth()
    alt no token
        F-->>U: redirect /unauthorized
    else token found
        F->>B: fetch with Bearer header
    end

    U->>F: open WebSocket
    F->>B: connect ws?token=<jwt>
    B->>B: get_ws_user dependency extracts + verifies token
    Note over B: oauth2_scheme not used (incompatible with WS upgrade)
    alt invalid/expired token
        B-->>F: connection rejected before accept
    else valid token
        B-->>F: connection accepted
    end
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
ollama pull hermes3
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
  ✓ Week 6 — Rolling summary (every 20 turns → campaigns.summary)
  ░ Week 7 — Entity extraction (Celery background tasks)
  ✓ Week 8 — Campaign dashboard with entity log

MONTH 3 — MULTIPLAYER
  ✓ Week 9  — WebSocket rooms + Redis pub/sub
              + round buffer (player actions staged, flushed via /gm resolve)
              + WebSocket streaming of GM response to all room participants
  ░ Week 10 — WebSocket auth hardening
              · replace oauth2_scheme with custom get_ws_user dependency
              · extract JWT from ?token= query param
              · reject connection before accept on invalid/expired token

              Multiplayer UI
              · Room lobby page — invite code display, player list,
                ready state per player, host-only Start button
              · Game view — shared narration panel + per-player action input
              · Live presence indicators (● connected / ○ disconnected)
              · Player sidebar — mini character cards for full party

              GM pipeline multiplayer support
              · Switch GM model to hermes3 (extended thinking + narration)
              · party_context block injected into all GM prompts
                (all player characters included, not just the sender)
              · fetch_character tool updated to return full party roster
              · GM response broadcast to all room WebSockets via pub/sub

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
| hermes3 | https://ollama.com/library/hermes3 |
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