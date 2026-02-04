# Stock Analysis MVP - Project Context

## Project Overview
SEC 10-K report analyzer for S&P 100 companies using Google Gemini for AI-powered risk assessment and summarization.

## Quick Start
```bash
# Backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Tech Stack
- **Backend:** FastAPI + SQLAlchemy + SQLite
- **Frontend:** Next.js 14 + shadcn/ui + TanStack Table + Recharts
- **AI:** Google Gemini 1.5 Flash
- **Data:** SEC EDGAR via edgartools library

## Key Files

### Backend
| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI app entry point |
| `backend/app/services/sec_fetcher.py` | Fetches 10-K filings from SEC EDGAR |
| `backend/app/services/gemini_analyzer.py` | Analyzes filings with Gemini API |
| `backend/app/models.py` | SQLAlchemy database models |
| `backend/app/routers/jobs.py` | Background job endpoints |

### Frontend
| File | Purpose |
|------|---------|
| `frontend/app/page.tsx` | Dashboard with stats and charts |
| `frontend/app/companies/page.tsx` | Company list table |
| `frontend/app/companies/[ticker]/page.tsx` | Company detail with risk scores |
| `frontend/app/admin/page.tsx` | Manual fetch/analyze triggers |

## API Endpoints
```
GET  /api/companies              - List companies with risk scores
GET  /api/companies/{ticker}     - Company details + filings
POST /api/jobs/fetch-all         - Trigger SEC data fetch
POST /api/jobs/analyze-all       - Trigger Gemini analysis
GET  /api/jobs/status            - Check job progress
```

## Database Tables
- `companies` - S&P 100 company info (ticker, CIK, name, sector)
- `filings` - SEC 10-K filings with raw content
- `analysis_results` - Gemini-generated summaries
- `risk_assessments` - Risk scores by category (1-10)

## Risk Categories
1. **Operational** - Supply chain, cybersecurity, process failures
2. **Financial** - FX exposure, interest rates, liquidity
3. **Regulatory** - Compliance, environmental, data privacy
4. **Strategic** - Competition, disruption, concentration
5. **Reputational** - Climate, social responsibility, ESG

## Environment Variables
```bash
# Backend (.env)
GEMINI_API_KEY=your_key_here
SEC_USER_AGENT="AppName your@email.com"
DATABASE_URL=sqlite:///./stock_analysis.db

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Error Codes (for debugging)
| Code | Component | Fix |
|------|-----------|-----|
| `SEC_RATE_LIMIT` | sec_fetcher | Wait 60s, retry |
| `SEC_FILING_NOT_FOUND` | sec_fetcher | Skip company |
| `GEMINI_API_ERROR` | gemini_analyzer | Check API key |
| `GEMINI_PARSE_ERROR` | gemini_analyzer | Retry with stricter prompt |

## Commands
```bash
# Run backend tests
cd backend && pytest -v

# Run frontend tests
cd frontend && npm test

# Check structured logs
cat backend/logs/structured.jsonl | jq .
```

## Implementation Status

### Phase 1: MVP Core
- [ ] Backend setup (FastAPI + SQLite)
- [ ] SEC fetcher service
- [ ] Gemini analyzer service
- [ ] Core API endpoints
- [ ] Frontend setup (Next.js)
- [ ] Company list page
- [ ] Company detail page
- [ ] Admin page

### Phase 2: Full Features
- [ ] Background job processing
- [ ] Dashboard with charts
- [ ] Risk drill-down
- [ ] Structured logging
- [ ] Unit tests
- [ ] E2E tests

## Important Notes
- SEC EDGAR rate limit: 10 requests/second
- Gemini context limit: ~15K tokens per section
- No authentication for MVP
- Manual trigger for data loading (admin page)

## Documentation
- [Architecture](docs/ARCHITECTURE.md) - System design, schema, tech stack
- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md) - Step-by-step build guide
