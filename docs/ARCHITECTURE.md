# Stock Analysis MVP - Architecture Plan

## Overview
A streamlined application to fetch SEC 10-K reports for top 100 companies, analyze them using Google Gemini, and display results in a modern dashboard.

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Data Loading | **Manual trigger** | Admin clicks button to fetch all 100 companies |
| LLM Model | **Gemini 1.5 Flash** | Fast & cheap (~$0.075/1M tokens) |
| Authentication | **None** | Open access for MVP simplicity |

---

## Tech Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Frontend | Next.js 14 + React | Full-stack, simple deployment |
| UI Components | shadcn/ui + Tailwind | Modern, lightweight |
| Data Tables | TanStack Table | Free, sufficient for MVP |
| Charts | Recharts | Simple, React-native |
| Backend | FastAPI | Python ecosystem for NLP |
| Database | SQLite | Simple for MVP |
| LLM | Google Gemini API | Summarization & analysis |
| SEC Data | edgartools library | Best Python SEC library |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │Dashboard │  │Companies │  │ Company  │  │ Risk Assessment  │ │
│  │ Overview │  │  Table   │  │  Detail  │  │     Charts       │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │ API Calls
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ REST API     │  │ Background   │  │ Analysis Service       │ │
│  │ Endpoints    │  │ Jobs         │  │ (Gemini Integration)   │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
          │                    │                      │
          ▼                    ▼                      ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Database   │    │   SEC EDGAR      │    │  Google Gemini   │
│   (SQLite)   │    │   (edgartools)   │    │      API         │
└──────────────┘    └──────────────────┘    └──────────────────┘
```

---

## Database Schema

```sql
-- Companies table
CREATE TABLE companies (
    id INTEGER PRIMARY KEY,
    cik TEXT UNIQUE NOT NULL,
    ticker TEXT NOT NULL,
    name TEXT NOT NULL,
    sector TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SEC Filings table
CREATE TABLE filings (
    id INTEGER PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    filing_type TEXT NOT NULL,
    filing_date DATE NOT NULL,
    fiscal_year INTEGER,
    accession_number TEXT UNIQUE,
    filing_url TEXT,
    raw_content TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analysis Results table
CREATE TABLE analysis_results (
    id INTEGER PRIMARY KEY,
    filing_id INTEGER REFERENCES filings(id),
    summary TEXT,
    risk_factors_text TEXT,
    mda_text TEXT,
    analysis_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Risk Assessments table
CREATE TABLE risk_assessments (
    id INTEGER PRIMARY KEY,
    filing_id INTEGER REFERENCES filings(id),
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    score INTEGER,
    description TEXT,
    key_risks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## API Endpoints

### Companies
- `GET /api/companies` - List all companies with latest risk scores
- `GET /api/companies/{ticker}` - Get company details + all filings

### Filings
- `GET /api/filings` - List all filings (paginated)
- `GET /api/filings/{id}` - Get filing details + analysis

### Analysis
- `GET /api/analysis/{filing_id}` - Get analysis results for a filing
- `GET /api/risk-summary` - Aggregated risk data for dashboard

### Admin/Jobs
- `POST /api/jobs/fetch-all` - Fetch all S&P 100 filings
- `POST /api/jobs/analyze-all` - Run Gemini analysis on pending filings
- `GET /api/jobs/status` - Check background job progress

---

## Frontend Routes

```
/                           → Dashboard (overview)
/companies                  → Company list with table
/companies/[ticker]         → Company detail + filing history
/risk                       → Risk assessment overview (charts)
/admin                      → Manual data fetch & analysis triggers
```

---

## Project Structure

```
stockanalysisv2/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── logging_config.py
│   │   ├── routers/
│   │   │   ├── companies.py
│   │   │   ├── filings.py
│   │   │   ├── analysis.py
│   │   │   └── jobs.py
│   │   └── services/
│   │       ├── sec_fetcher.py
│   │       ├── gemini_analyzer.py
│   │       └── risk_calculator.py
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── companies/
│   │   ├── risk/
│   │   └── admin/
│   ├── components/
│   ├── lib/
│   └── package.json
│
├── docs/
│   ├── ARCHITECTURE.md
│   └── IMPLEMENTATION_PLAN.md
│
├── data/
│   └── sp100_companies.json
│
└── CLAUDE.md
```

---

## Risk Categories

1. **Operational Risk** - Supply chain, cybersecurity, process failures
2. **Financial/Market Risk** - FX exposure, interest rates, liquidity
3. **Regulatory Risk** - Compliance, environmental, data privacy
4. **Strategic Risk** - Competition, disruption, concentration
5. **Reputational/ESG Risk** - Climate, social responsibility, governance
