<p align="center">
  <h1 align="center">NAYAM (नयम्)</h1>
  <p align="center"><strong>AI Co-Pilot Platform for Public Leaders & Municipal Administrators</strong></p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?logo=python" />
  <img src="https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi" />
  <img src="https://img.shields.io/badge/Next.js-16-black?logo=next.js" />
  <img src="https://img.shields.io/badge/LLM-Groq%20Llama%203.3-orange" />
  <img src="https://img.shields.io/badge/RAG-TF--IDF-green" />
  <img src="https://img.shields.io/badge/STT-Whisper-blueviolet" />
  <img src="https://img.shields.io/badge/Routers-16-blue" />
  <img src="https://img.shields.io/badge/Tests-518%20passing-brightgreen" />
</p>

---

## What is NAYAM?

NAYAM is an **AI-powered governance platform** that helps municipal leaders, staff, and analysts manage citizens, grievances, policy documents, schedules, and administrative workflows through an intelligent multi-agent system with speech-to-text input, AI draft generation, and smart notifications.

**Core capabilities:**

- 🤖 **Multi-Agent Intelligence** — 3 specialized AI agents (Policy, Citizen, Operations) powered by Groq LLM with intent-based routing
- 📄 **Document RAG Pipeline** — Upload PDF/DOCX/TXT → text extraction → chunking → TF-IDF retrieval → LLM-grounded answers
- 🎤 **Speech-to-Text Pipeline** — Fully implemented multi-provider STT: Groq Whisper (primary) → local faster-whisper (offline fallback) → OpenAI (last resort). Transcribe, classify, and ingest voice into RAG
- ✍️ **AI Draft Generator** — LLM-powered generation of 9 document types (Speeches, Official Responses, Press Releases, Policy Briefs, Meeting Agendas, Public Notices, Letters, RTI Responses, Circulars) with template system prompts, tone/audience control, and versioned editing
- 📅 **Schedule Management** — Full calendar/event system for leaders: meetings, hearings, site visits, deadlines, reviews, public events with priority levels, status lifecycle, and department/ward assignment
- 🔔 **Smart Notifications** — Aggregated notification feed pulling from pending approvals, high-priority issues, recent documents, and upcoming events (48-hour lookahead)
- ✅ **Human-in-the-Loop Approvals** — Every AI-proposed action requires explicit human approval before execution
- 📊 **Real-time Analytics** — Ward-level risk scoring, predictive insights, geo-spatial intelligence
- 🔒 **Enterprise Security** — JWT auth, RBAC (Leader/Staff/Analyst), rate limiting, audit logging

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 16)                     │
│  Dashboard │ Issues │ Citizens │ Documents │ Intelligence    │
│  Schedule │ Drafts │ Approvals │ Geo-Analytics │ Predictive │
│  Compliance │ Monitoring │ Settings │ Notifications 🔔      │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API (JSON)
┌──────────────────────────▼──────────────────────────────────┐
│                    BACKEND (FastAPI)                          │
│                                                              │
│  ┌─────────┐  ┌──────────┐  ┌────────────┐  ┌───────────┐  │
│  │ 16 API  │→ │ Services │→ │Repositories│→ │ SQLAlchemy│  │
│  │ Routers │  │ (Logic)  │  │ (Data)     │  │   ORM     │  │
│  └─────────┘  └──────────┘  └────────────┘  └─────┬─────┘  │
│                                                     │        │
│  ┌──────────────────────────────────────────────────┤        │
│  │         AI / INTELLIGENCE LAYER                  │        │
│  │                                                  │        │
│  │  ┌─────────┐  ┌──────────┐  ┌────────────────┐  │        │
│  │  │ Agent   │→ │ 3 Agents │→ │ Groq LLM       │  │        │
│  │  │ Router  │  │ P / C / O│  │ (llama-3.3-70b)│  │        │
│  │  └─────────┘  └──────────┘  └────────────────┘  │        │
│  │                                                  │        │
│  │  ┌──────────────────────────────────────────┐    │        │
│  │  │         RAG Pipeline                     │    │        │
│  │  │  Upload → Extract → Chunk → TF-IDF Store │    │        │
│  │  │  Query  → Vectorize → Cosine Sim → Top-K │    │        │
│  │  └──────────────────────────────────────────┘    │        │
│  │                                                  │        │
│  │  ┌──────────────────────────────────────────┐    │        │
│  │  │    STT Pipeline (Fully Implemented)       │    │        │
│  │  │  Audio → Groq Whisper / faster-whisper   │    │        │
│  │  │  Transcript → Classify → Ingest → RAG    │    │        │
│  │  └──────────────────────────────────────────┘    │        │
│  │                                                  │        │
│  │  ┌──────────────────────────────────────────┐    │        │
│  │  │    AI Draft Generator                    │    │        │
│  │  │  9 Templates → Groq LLM → Versioned Docs│    │        │
│  │  └──────────────────────────────────────────┘    │        │
│  └──────────────────────────────────────────────────┘        │
│                                                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │   SQLite    │
                    │  (dev) /    │
                    │ PostgreSQL  │
                    │  (prod)     │
                    └─────────────┘
```

### Backend Structure

```
app/
├── agents/           # Multi-agent framework (Policy, Citizen, Operations)
│   ├── base.py       # BaseAgent ABC, Groq LLM client, prompt builder
│   ├── router.py     # Intent-based keyword routing
│   ├── policy.py     # PolicyAgent — governance, schemes, regulations
│   ├── citizen.py    # CitizenAgent — complaints, ward analytics
│   └── operations.py # OperationsAgent — resources, departments, KPIs
├── api/v1/           # 16 REST API routers
│   ├── auth.py       # JWT register/login
│   ├── citizens.py   # CRUD + search
│   ├── issues.py     # CRUD + filters
│   ├── documents.py  # Upload + RAG indexing
│   ├── dashboard.py  # Aggregated analytics
│   ├── agent.py      # Chat + session history
│   ├── actions.py    # HITL approval workflow
│   ├── stt.py        # Speech-to-text (transcribe, classify, ingest)
│   ├── notifications.py # Aggregated notification feed
│   ├── schedule.py   # Calendar / event CRUD
│   ├── drafts.py     # AI draft generation + management
│   ├── sync.py       # Offline data sync
│   ├── offline.py    # Offline queue management
│   ├── compliance.py # Audit exports
│   ├── monitoring.py # Health probes + metrics
│   └── hardening.py  # Rate limit admin
├── models/           # 9 SQLAlchemy ORM models (24+ tables)
│   ├── user.py       # User model with roles
│   ├── citizen.py    # Citizen records
│   ├── issue.py      # Grievance/issue tracking
│   ├── document.py   # Uploaded documents
│   ├── event.py      # Schedule/calendar events
│   └── draft.py      # AI-generated drafts
├── schemas/          # 20+ Pydantic v2 request/response schemas
├── repositories/     # Data access layer (query builders)
├── services/         # Business logic layer
│   ├── agent.py      # Orchestrates: route → RAG → execute → persist → approve
│   ├── memory.py     # Conversation storage + TF-IDF RAG search
│   ├── document.py   # Text extraction, chunking, Groq summarization
│   ├── stt.py        # Multi-provider STT (Groq/local/OpenAI Whisper)
│   ├── notification.py # Aggregation from 4 sources
│   ├── schedule.py   # Event lifecycle management
│   └── draft.py      # LLM-powered draft generation (9 templates)
├── core/             # Config, DB engine, JWT security, structured logging
├── compliance/       # Audit trail + GDPR export
├── monitoring/       # Prometheus metrics + request logging
├── hardening/        # Rate limiting middleware
├── offline/          # Offline-first queue
└── sync/             # Conflict resolution engine
```

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | Next.js 16, React 19, TypeScript 5.7 | UI framework |
| **UI Components** | Radix UI, Tailwind CSS 4, Recharts | Accessible components + charts |
| **Backend** | FastAPI 0.104, Python 3.13 | REST API framework |
| **ORM** | SQLAlchemy 2.0, Alembic | Database + migrations |
| **Database** | SQLite (dev) / PostgreSQL 16 (prod) | Persistence |
| **LLM** | Groq SDK → Llama 3.3 70B Versatile | Agent intelligence |
| **RAG** | scikit-learn TF-IDF + cosine similarity | Document retrieval |
| **Doc Extraction** | PyPDF2, python-docx | PDF/DOCX text extraction |
| **STT** | Groq Whisper + faster-whisper (local) + OpenAI Whisper | Multi-provider speech-to-text with fallback chain |
| **Auth** | python-jose (JWT) + passlib (bcrypt) | Authentication |
| **Logging** | structlog + JSON output | Observability |
| **Monitoring** | Prometheus client | Metrics |
| **Deployment** | Docker, docker-compose, Nginx | Containerization |

---

## AI & RAG Pipeline

### Document Ingestion

```
File Upload (.pdf/.docx/.txt)
       │
       ▼
  extract_text()          ← PyPDF2 / python-docx / raw read
       │
       ▼
  chunk_text()            ← 400-word chunks, 50-word overlap
       │
       ├──▶ generate_summary()  → Groq LLM → 2-3 sentence summary
       │
       ▼
  store_embedding()       ← Each chunk → embeddings table (SHA-256 dedup)
```

### RAG Retrieval (on user query)

```
User Query
       │
       ▼
  search_by_text()        ← Load all stored chunks from DB
       │
       ▼
  TfidfVectorizer         ← Build vocabulary on-the-fly
       │
       ▼
  cosine_similarity()     ← Rank chunks by relevance
       │
       ▼
  Top-5 chunks (score > 0.02)  → Injected into agent prompt
       │
       ▼
  Groq LLM                ← Generates grounded response
```

### Speech-to-Text Pipeline (Fully Implemented)

```
User speaks into microphone (🎤 button on Intelligence / Documents pages)
       │
       ▼
  Audio capture (MediaRecorder API → .webm/.wav)
       │
       ▼
  POST /api/v1/stt/transcribe   ← or /classify or /ingest
       │
       ▼
  STT Provider Chain:
    1. Groq Whisper (primary, fastest)
    2. Local faster-whisper small (offline fallback, CPU/int8)
    3. OpenAI Whisper API (last resort)
       │
       ▼
  Text transcript + language detection + duration
       │
       ├──▶ /transcribe: Returns text only
       ├──▶ /classify:   Transcribe → LLM classifies content type
       └──▶ /ingest:     Transcribe → Classify → Create entity → RAG index
```

**Supported formats:** .wav, .mp3, .m4a, .ogg, .webm, .flac, .aac (max 25 MB)

The STT pipeline fully integrates with the existing RAG system — transcribed voice content enters `chunk_text()` → `store_embedding()` → `search_by_text()` making spoken content searchable alongside uploaded documents.

### AI Draft Generator

```
User selects template type (9 types available)
       │
       ▼
  POST /api/v1/drafts/generate
       │
       ▼
  Template system prompt selected (tone + audience placeholders)
       │
       ▼
  Groq LLM (llama-3.3-70b, temperature=0.7, max_tokens=2000)
       │
       ▼
  Draft created with content, word count, version=1
       │
       ▼
  Edit → version auto-incremented → Submit for Review → Approve → Publish
```

**9 Draft Types:** Speech, Official Response, Press Release, Policy Brief, Meeting Agenda, Public Notice, Formal Letter, RTI Response, Government Circular

### Schedule Management

```
Leader creates event with type/priority/attendees/department
       │
       ▼
  Lifecycle: Scheduled → In Progress → Completed (or Cancelled)
       │
       ▼
  Smart notifications: Events within 48 hours surface in notification feed
```

**7 Event Types:** Meeting, Hearing, Site Visit, Deadline, Review, Public Event, Other

---

## Multi-Agent System

| Agent | Handles | Example Queries |
|---|---|---|
| **PolicyAgent** | Governance policies, schemes, regulations | *"What is the water supply SLA?"* |
| **CitizenAgent** | Citizen records, complaints, ward analytics | *"Open complaints in Ward-3?"* |
| **OperationsAgent** | Resources, departments, KPIs, scheduling | *"Allocate road repair crew"* |

**Routing:** Keyword-scored intent classification → highest-scoring agent handles the query. Default fallback: CitizenAgent.

**HITL Safety:** Any agent-proposed mutation (escalate priority, allocate resources, close issue) creates an `ActionRequest` requiring human approval before execution.

---

## API Endpoints

### Core CRUD
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/auth/register` | User registration |
| `POST` | `/api/v1/auth/login` | JWT login |
| `CRUD` | `/api/v1/citizens/` | Create / List / Get / Update / Delete citizens |
| `CRUD` | `/api/v1/issues/` | Create / List / Get / Update / Delete issues |
| `POST` | `/api/v1/documents/upload` | Upload + RAG index document |
| `GET` | `/api/v1/documents/` | List documents |
| `GET` | `/api/v1/dashboard/` | Aggregated analytics |

### Intelligence
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/agent/query` | Send query to AI agent |
| `GET` | `/api/v1/agent/agents` | List available agents |
| `GET` | `/api/v1/agent/sessions/{id}` | Conversation history |

### Approvals (HITL)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/actions/` | List action requests |
| `GET` | `/api/v1/actions/pending` | Pending approvals |
| `POST` | `/api/v1/actions/{id}/review` | Approve / reject action |

### Speech-to-Text
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/stt/transcribe` | Audio → text transcription |
| `POST` | `/api/v1/stt/classify` | Audio → text → content classification |
| `POST` | `/api/v1/stt/ingest` | Audio → text → classify → create entity → RAG index |

### Schedule Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/schedule/` | List events (filters: status, type, department, date range) |
| `POST` | `/api/v1/schedule/` | Create event (Leader/Staff) |
| `GET` | `/api/v1/schedule/{id}` | Get event by ID |
| `PATCH` | `/api/v1/schedule/{id}` | Update event |
| `DELETE` | `/api/v1/schedule/{id}` | Delete event |
| `GET` | `/api/v1/schedule/upcoming/list` | Upcoming events |

### AI Draft Generator
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/drafts/generate` | Generate draft with AI (Leader/Staff) |
| `GET` | `/api/v1/drafts/` | List drafts (filters: type, status, department) |
| `GET` | `/api/v1/drafts/{id}` | Get draft by ID |
| `PATCH` | `/api/v1/drafts/{id}` | Update draft (auto-increments version) |
| `DELETE` | `/api/v1/drafts/{id}` | Delete draft |

### Notifications
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/notifications/` | Aggregated notification feed (4 sources) |

### Platform
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/sync/push` | Push offline data |
| `POST` | `/api/v1/sync/pull` | Pull latest data |
| `GET` | `/api/v1/compliance/exports` | Audit trail exports |
| `GET` | `/api/v1/monitoring/metrics` | Prometheus metrics |

---

## Quick Start

### Prerequisites
- Python 3.13+
- Node.js 18+
- Groq API key → [console.groq.com](https://console.groq.com)

### Backend

```bash
git clone https://github.com/Sakshamyadav15/Nayam.git
cd Nayam

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

pip install -r requirements.txt

# Create .env with GROQ_API_KEY, JWT_SECRET_KEY, DATABASE_URL
uvicorn app.main:app --reload --port 8000

# Seed data (server must be running)
python seed_database.py         # 60 citizens, 130 issues, 5 docs
python seed_extras.py           # Date spread + 16 action requests
python seed_schedule_drafts.py  # 22 events + 9 AI drafts
```

### Frontend

```bash
cd frontend
npm install
npm run dev                     # → http://localhost:3000
```

### Default Login
```
Email:    admin@nayam.gov.in
Password: admin12345
```

### Docker

```bash
docker-compose up -d            # PostgreSQL + Backend + Nginx
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./nayam_dev.db` | Database URI |
| `JWT_SECRET_KEY` | — | JWT signing secret |
| `GROQ_API_KEY` | — | Groq LLM API key |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | LLM model |
| `UPLOAD_DIR` | `./uploads` | File upload path |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | CORS origins |
| `APP_ENV` | `development` | Environment mode |
| `MAX_UPLOAD_SIZE_MB` | `10` | Upload size limit |
| `RATE_LIMIT_MAX_REQUESTS` | `100` | Rate limit per window |

---

## Testing

```bash
pytest -v                       # All 518 tests
pytest tests/test_auth.py       # Auth module
pytest tests/test_documents.py  # Document + RAG tests
pytest tests/test_integration.py # Integration tests
```

---

## Security

- **JWT Authentication** with configurable token expiry
- **RBAC** — Leader / Staff / Analyst role hierarchy
- **Per-IP Rate Limiting** — Sliding window with audit trail
- **Pydantic v2 Validation** on every endpoint
- **File Security** — Extension whitelist, size limits, UUID filenames
- **HITL Guardrails** — AI cannot mutate state without human approval
- **Structured Logging** — Request-ID correlation, JSON output in production
- **No Hardcoded Secrets** — All sensitive config from environment

---

## License

Internal — Not for public distribution.
