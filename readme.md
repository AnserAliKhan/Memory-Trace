# ReFound — Rediscover what you already know.

ReFound is a **local-first memory retrieval system**. Import your ChatGPT exports, Markdown notes, text files, and PDFs — then ask questions about what you already know.

---

## Features

- 📥 **Import** ChatGPT JSON exports, Markdown, TXT, PDF
- 🔍 **Semantic search** over your personal knowledge base
- 🧠 **Memory Assistant** — Gemini synthesizes answers from retrieved chunks
- 🔁 **Similar Problem Detector** — "You solved this before"
- 📌 **Source Citations** — every answer traces back to a document
- 💾 **100% local** — SQLite + FAISS, no cloud, no telemetry

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React + Vite + TypeScript + TailwindCSS |
| Backend | FastAPI + Python 3.12+ |
| Database | SQLite + SQLAlchemy |
| Embeddings | BAAI/bge-small-en-v1.5 |
| Vector Search | FAISS |
| Reranking | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| LLM | Gemini API |

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Git

### 1. Clone

```bash
git clone https://github.com/yourname/refound.git
cd refound
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
cp ../.env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Run (Development)

**Terminal 1 — Backend:**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

---

## Project Structure

```
refound/
├── backend/
│   ├── parsers/          # File type parsers (PDF, MD, TXT, ChatGPT JSON)
│   ├── processors/       # Chunking and cleaning
│   ├── database/         # SQLAlchemy models and DB session
│   ├── embeddings/       # BAAI embedding pipeline
│   ├── retrieval/        # FAISS index management
│   ├── reranking/        # Cross-encoder reranker
│   ├── llm/              # Gemini API integration
│   ├── api/              # FastAPI route handlers
│   ├── tests/            # pytest test suite
│   ├── main.py           # App entrypoint
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # Reusable UI components
│   │   ├── pages/        # Home, Import, Results, Settings
│   │   ├── hooks/        # Custom React hooks
│   │   ├── services/     # API client
│   │   └── types/        # TypeScript types
│   ├── index.html
│   └── package.json
├── .env.example
└── docker-compose.yml
```

---

## Environment Variables

See `.env.example`. Only required variable is `GEMINI_API_KEY`.

---

## Docker (Optional)

```bash
docker-compose up --build
```

---

## Deployment (prod, PR previews, UAT)

The frontend is hosted on Cloudflare Pages: production from `main`, a preview per PR, and a
UAT site with all open PRs merged together. The backend runs on each tester's machine. See
[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

---

## Testing

```bash
cd backend
pytest tests/ -v
```

---

## License

MIT