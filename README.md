# AI-Powered Anomaly, Fraud, and Inefficiency Detection Platform for MPLAD Scheme Implementation

An end-to-end, production-ready full-stack web application developed for the **Smart India Hackathon (SIH)**. This platform applies machine learning (Isolation Forest, TF-IDF Cosine Similarity) and local LLM generative auditing (Ollama) to detect cost overruns, duplicate work descriptions, timeline delays, and contractor monopolies in India's **MPLAD (Members of Parliament Local Area Development)** scheme implementation.

---

## Architecture Overview

* **Frontend (Web Client):** React 18, Vite Framework, Tailwind CSS, Lucide React Icons, Recharts Data Visualization, Axios, React Router DOM v6.
* **Backend (Web Server API):** Python FastAPI, CORS Middleware, Async SQLAlchemy ORM (`asyncpg` / `aiosqlite`), Pydantic v2.
* **Database:** PostgreSQL (Fully normalized 3NF Schema) with automatic fallback to local SQLite for instant zero-config testing.
* **ML & AI Engine:** Scikit-learn (Isolation Forest for financial multi-variate outliers, TF-IDF + Cosine Similarity for duplicate proposal text detection), plus an async HTTP client connecting to local Ollama LLM (`http://localhost:11434`).

---

## Directory Structure

```
Prototype/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py         # Async SQLAlchemy engine (PostgreSQL/SQLite)
│   │   ├── models.py           # 3NF ORM models (mps, districts, contractors, projects, etc.)
│   │   ├── schemas.py          # Pydantic v2 schemas
│   │   ├── ml_engine.py        # Isolation Forest & TF-IDF Cosine similarity detector
│   │   ├── llm_service.py      # Ollama HTTP client & audit report generator
│   │   ├── main.py             # FastAPI app with CORS middleware
│   │   └── routers/
│   │       ├── seed.py         # POST /api/seed
│   │       ├── dashboard.py    # GET /api/dashboard/kpis
│   │       └── projects.py     # GET /api/projects/anomalies, POST /api/projects/analyze, GET /api/projects/{id}/explain
│   ├── requirements.txt
│   └── schema.sql              # Raw 3NF DDL PostgreSQL schema
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/         # Layout, Navbar, Sidebar, StatCard
│   │   ├── pages/              # Executive Dashboard, Audit Table, Live Analyzer
│   │   ├── services/           # Axios API client (http://localhost:8000/api)
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css           # Glassmorphism & dark theme styles
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
├── scripts/
│   └── seed_db.py              # Standalone 1,000+ record dataset generator
├── .env.example
└── README.md
```

---

## Step-by-Step Setup Instructions

### Prerequisites
* Python 3.10+
* Node.js 18+ and npm
* PostgreSQL (Optional - SQLite fallback supported out-of-the-box)
* Ollama (Optional for AI reports - fallback generator included)

---

### Step 1: Database Configuration & Setup

#### Option A: PostgreSQL Setup (Recommended for Production)
1. Ensure PostgreSQL is running locally on port `5432`.
2. Create the target database:
   ```bash
   createdb -U postgres mplads_db
   ```
3. Copy `.env.example` to `.env` in the root directory:
   ```bash
   cp .env.example .env
   ```
4. Verify `DATABASE_URL` matches your PostgreSQL password:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/mplads_db
   ```

#### Option B: Zero-Config Local SQLite Mode
If PostgreSQL is not installed, set `DATABASE_URL` in `.env`:
```env
DATABASE_URL=sqlite+aiosqlite:///./mplads.db
```

---

### Step 2: Backend API Server Setup

1. Open terminal and navigate to `backend/`:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   # Windows PowerShell:
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS:
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install required backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI development web server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   * The API server will start at `http://localhost:8000`.
   * Interactive OpenAPI / Swagger docs are available at `http://localhost:8000/docs`.

---

### Step 3: Seed Database with 1,000+ Realistic MPLADS Records

Open a new terminal window, activate the virtual environment, and run:
```bash
python scripts/seed_db.py
```
*Alternatively*, trigger database re-seeding directly from the running web interface by clicking the **"Re-Seed Data"** button in the top navbar or posting to `POST http://localhost:8000/api/seed`.

---

### Step 4: Frontend React Web Client Setup

1. Open a new terminal window and navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Start Vite React development server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to:
   ```
   http://localhost:5173
   ```

---

### Step 5: Start Local Ollama LLM Service (Optional)

To enable live LLM executive audit reports:
1. Install [Ollama](https://ollama.com/).
2. Pull and start the `llama3` model:
   ```bash
   ollama pull llama3
   ollama run llama3
   ```
3. The backend connects asynchronously to `http://localhost:11434/api/generate`. If Ollama is offline, the backend automatically uses an intelligent domain-specific fallback generator.

---

## Key Web Application API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/seed` | Drops/re-creates database tables and populates 1,000+ synthetic MPLADS records. |
| `GET` | `/api/dashboard/kpis` | Returns aggregated statistics (total funds, suspended value, category variance, district rankings). |
| `GET` | `/api/projects/anomalies` | Paginated and filterable endpoint listing flagged high-risk projects. |
| `POST` | `/api/projects/analyze` | Real-time web proposal submission endpoint evaluating ML Isolation Forest & TF-IDF models. |
| `GET` | `/api/projects/{id}/explain` | Triggers local Ollama LLM to return a 2-sentence executive audit summary. |

---

## Verification & Testing Checklist

- [x] Backend imports compile cleanly without errors.
- [x] Database tables create successfully via async SQLAlchemy.
- [x] Database seeder creates 1,000+ project records with synthetic anomaly injections.
- [x] Recharts components render responsive donut, bar, and area charts.
- [x] Slide-over drawer panel loads live AI audit report.
- [x] Proposal form submission returns instant ML risk score banner.
