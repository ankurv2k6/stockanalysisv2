# Stock Analysis MVP - Implementation Plan

## Phase Overview

| Phase | Goal | Deliverables |
|-------|------|--------------|
| **Phase 1** | MVP Core | End-to-end flow for 1 company |
| **Phase 2** | Full Features | 100 companies, charts, logging, tests |

---

# Phase 1: MVP Core

**Goal:** Get a working end-to-end flow for 1 company

## Step 1.1: Backend Project Setup
**Files to create:**
- `backend/app/__init__.py`
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/requirements.txt`
- `backend/.env.example`

**Tasks:**
```bash
# Create backend folder structure
mkdir -p backend/app/routers backend/app/services

# Initialize FastAPI app
# main.py should have:
# - FastAPI() instance
# - CORS middleware
# - Health check endpoint
# - Router includes
```

**Verification:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# Visit http://localhost:8000/docs
```

---

## Step 1.2: Database Models & Connection
**Files to create:**
- `backend/app/database.py`
- `backend/app/models.py`
- `backend/app/schemas.py`

**Tasks:**
1. Set up SQLAlchemy with SQLite
2. Create Company, Filing, AnalysisResult, RiskAssessment models
3. Create Pydantic schemas for API responses
4. Add database initialization on startup

**Key Code - database.py:**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./stock_analysis.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Verification:**
```bash
# Run app, check that stock_analysis.db is created
ls -la *.db
```

---

## Step 1.3: SEC Fetcher Service
**Files to create:**
- `backend/app/services/sec_fetcher.py`
- `backend/data/sp100_companies.json`

**Tasks:**
1. Install edgartools: `pip install edgartools`
2. Create SECFetcher class with methods:
   - `fetch_company_info(ticker)` - Get CIK and company name
   - `fetch_10k(ticker)` - Get latest 10-K filing
   - `extract_sections(filing)` - Extract Item 1A, Item 7
3. Add S&P 100 ticker list to data folder

**Key Code - sec_fetcher.py:**
```python
from edgar import Company, set_identity

class SECFetcher:
    def __init__(self, user_agent: str):
        set_identity(user_agent)

    def fetch_10k(self, ticker: str):
        company = Company(ticker)
        filings = company.get_filings(form="10-K").latest(1)
        return filings[0] if filings else None

    def extract_sections(self, filing):
        tenk = filing.obj()
        return {
            "risk_factors": str(tenk.item1a)[:50000],
            "mda": str(tenk.item7)[:50000],
            "business": str(tenk.item1)[:20000]
        }
```

**Verification:**
```python
# Test in Python REPL
from app.services.sec_fetcher import SECFetcher
fetcher = SECFetcher("MyApp myemail@example.com")
filing = fetcher.fetch_10k("AAPL")
print(filing.accession_number)
```

---

## Step 1.4: Gemini Analyzer Service
**Files to create:**
- `backend/app/services/gemini_analyzer.py`

**Tasks:**
1. Install google-generativeai: `pip install google-generativeai`
2. Create GeminiAnalyzer class with methods:
   - `analyze(risk_factors, mda)` - Generate summary + risk scores
   - `_parse_response(text)` - Parse JSON from Gemini response

**Key Code - gemini_analyzer.py:**
```python
import google.generativeai as genai
import json

class GeminiAnalyzer:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def analyze(self, risk_factors: str, mda: str) -> dict:
        prompt = f"""Analyze this SEC 10-K filing and return JSON with:
        {{
            "summary": "3 paragraph executive summary",
            "risk_assessment": {{
                "operational": {{"score": 1-10, "risks": ["risk1", "risk2", "risk3"]}},
                "financial": {{"score": 1-10, "risks": [...]}},
                "regulatory": {{"score": 1-10, "risks": [...]}},
                "strategic": {{"score": 1-10, "risks": [...]}},
                "reputational": {{"score": 1-10, "risks": [...]}}
            }}
        }}

        Risk Factors: {risk_factors[:15000]}
        MD&A: {mda[:15000]}
        """

        response = self.model.generate_content(prompt)
        return self._parse_response(response.text)

    def _parse_response(self, text: str) -> dict:
        # Extract JSON from response
        start = text.find('{')
        end = text.rfind('}') + 1
        return json.loads(text[start:end])
```

**Verification:**
```python
# Test with sample text
from app.services.gemini_analyzer import GeminiAnalyzer
analyzer = GeminiAnalyzer("your-api-key")
result = analyzer.analyze("Sample risk factors...", "Sample MD&A...")
print(result)
```

---

## Step 1.5: Core API Endpoints
**Files to create:**
- `backend/app/routers/companies.py`
- `backend/app/routers/filings.py`
- `backend/app/routers/jobs.py`

**Tasks:**
1. Create `/api/companies` endpoints (GET list, GET by ticker)
2. Create `/api/filings` endpoints (GET list, GET by id)
3. Create `/api/jobs/fetch-all` endpoint (trigger SEC fetch)
4. Create `/api/jobs/analyze-all` endpoint (trigger Gemini analysis)
5. Wire up routers in main.py

**Key Code - jobs.py:**
```python
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.sec_fetcher import SECFetcher
from app.services.gemini_analyzer import GeminiAnalyzer

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

@router.post("/fetch-all")
async def fetch_all_filings(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(fetch_all_task, db)
    return {"status": "started", "message": "Fetching all filings"}

def fetch_all_task(db: Session):
    fetcher = SECFetcher(settings.SEC_USER_AGENT)
    # Load S&P 100 tickers
    # For each ticker: fetch 10-K, save to database
    pass
```

**Verification:**
```bash
curl http://localhost:8000/api/companies
curl -X POST http://localhost:8000/api/jobs/fetch-all
```

---

## Step 1.6: Frontend Setup
**Files to create:**
- `frontend/package.json`
- `frontend/app/layout.tsx`
- `frontend/app/page.tsx`
- `frontend/tailwind.config.js`
- `frontend/lib/api.ts`

**Tasks:**
```bash
# Create Next.js app
npx create-next-app@latest frontend --typescript --tailwind --eslint --app

# Install dependencies
cd frontend
npm install @tanstack/react-query @tanstack/react-table recharts lucide-react

# Initialize shadcn/ui
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card table
```

**Verification:**
```bash
cd frontend
npm run dev
# Visit http://localhost:3000
```

---

## Step 1.7: Company List Page
**Files to create:**
- `frontend/app/companies/page.tsx`
- `frontend/components/companies/CompanyTable.tsx`
- `frontend/lib/api.ts`

**Tasks:**
1. Create API client with fetch wrapper
2. Create TanStack Query hook for companies
3. Build CompanyTable component with sorting
4. Add navigation to company detail

**Verification:**
- Visit /companies
- See table with company data
- Click row to navigate to detail

---

## Step 1.8: Company Detail Page
**Files to create:**
- `frontend/app/companies/[ticker]/page.tsx`
- `frontend/components/company/CompanyHeader.tsx`
- `frontend/components/company/ExecutiveSummary.tsx`
- `frontend/components/company/RiskAssessment.tsx`

**Tasks:**
1. Create dynamic route for company detail
2. Fetch company + analysis data
3. Display executive summary
4. Display risk scores as horizontal bars

**Verification:**
- Visit /companies/AAPL
- See company info, summary, risk bars

---

## Step 1.9: Admin Page
**Files to create:**
- `frontend/app/admin/page.tsx`
- `frontend/components/admin/FetchButton.tsx`
- `frontend/components/admin/AnalyzeButton.tsx`

**Tasks:**
1. Create admin page with two action cards
2. "Fetch All Filings" button triggers POST /api/jobs/fetch-all
3. "Analyze All Pending" button triggers POST /api/jobs/analyze-all
4. Show status/progress indicator

**Verification:**
- Visit /admin
- Click "Fetch All Filings"
- See status update
- Check database has new records

---

## Phase 1 Milestone Checklist

- [ ] Backend starts without errors
- [ ] Can fetch 1 company from SEC EDGAR
- [ ] Can analyze filing with Gemini
- [ ] Company list shows in frontend
- [ ] Company detail shows summary + risk scores
- [ ] Admin page can trigger fetch/analyze

---

# Phase 2: Full Feature Set + Quality

## Step 2.1: Background Job Processing
**Tasks:**
1. Add job status tracking to database
2. Implement progress updates during batch processing
3. Add rate limiting (10 req/sec for SEC, respect Gemini limits)
4. Handle errors gracefully, continue with next company

---

## Step 2.2: Dashboard Page
**Files to create:**
- `frontend/app/page.tsx` (update)
- `frontend/components/dashboard/StatsCards.tsx`
- `frontend/components/dashboard/RiskPieChart.tsx`
- `frontend/components/dashboard/RecentHighRisk.tsx`

**Tasks:**
1. Create stats cards (total companies, analyzed, high risk, avg score)
2. Add pie chart for risk distribution
3. Add bar chart for risk by category
4. Add table of recent high-risk companies

---

## Step 2.3: Risk Drill-Down Charts
**Files to create:**
- `frontend/app/risk/page.tsx`
- `frontend/components/risk/CategoryChart.tsx`
- `frontend/components/risk/DrillDownTable.tsx`

**Tasks:**
1. Bar chart showing avg risk by category
2. Click category to drill down to companies
3. Sector comparison grouped bar chart

---

## Step 2.4: Table Filtering & Search
**Tasks:**
1. Add search input to company table
2. Add sector filter dropdown
3. Add risk level filter
4. Add column sorting

---

## Step 2.5: Structured Logging (Backend)
**Files to create:**
- `backend/app/logging_config.py`
- `backend/logs/.gitkeep`

**Tasks:**
1. Create StructuredLogger class
2. Log to both console and JSON file
3. Add error codes and suggested fixes
4. Integrate logging into all services

---

## Step 2.6: Frontend Logging
**Files to create:**
- `frontend/lib/logger.ts`

**Tasks:**
1. Create log function with structured format
2. Log API errors with context
3. Optional: send logs to backend in production

---

## Step 2.7: Unit Tests (Backend)
**Files to create:**
- `backend/tests/conftest.py`
- `backend/tests/unit/test_sec_fetcher.py`
- `backend/tests/unit/test_gemini_analyzer.py`
- `backend/tests/unit/test_risk_calculator.py`

**Tasks:**
1. Set up pytest with fixtures
2. Mock external APIs (SEC, Gemini)
3. Test happy paths and error cases

---

## Step 2.8: Integration Tests (Backend)
**Files to create:**
- `backend/tests/integration/test_api_companies.py`
- `backend/tests/integration/test_api_jobs.py`

**Tasks:**
1. Use TestClient for API tests
2. Set up test database
3. Test all endpoints

---

## Step 2.9: Frontend Tests
**Files to create:**
- `frontend/__tests__/components/CompanyTable.test.tsx`
- `frontend/__tests__/e2e/dashboard.spec.ts`
- `frontend/jest.config.js`
- `frontend/playwright.config.ts`

**Tasks:**
1. Set up Jest with React Testing Library
2. Write component unit tests
3. Set up Playwright for E2E
4. Write E2E tests for main flows

---

## Step 2.10: Error Handling & Loading States
**Tasks:**
1. Add loading skeletons to all pages
2. Add error boundaries
3. Add toast notifications for actions
4. Add retry logic for failed API calls

---

## Step 2.11: Responsive Design
**Tasks:**
1. Test all pages on mobile viewport
2. Make tables horizontally scrollable
3. Stack cards vertically on mobile
4. Adjust chart sizes for mobile

---

## Phase 2 Milestone Checklist

- [ ] All 100 companies can be fetched
- [ ] Dashboard shows aggregated stats
- [ ] Risk charts with drill-down work
- [ ] Table filtering and search work
- [ ] Logs are written in structured format
- [ ] Backend tests pass (>70% coverage)
- [ ] Frontend tests pass
- [ ] E2E tests pass
- [ ] Works on mobile devices

---

# Verification Commands

## Backend
```bash
cd backend

# Start server
uvicorn app.main:app --reload

# Run tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html

# Check logs
tail -f logs/app.log
cat logs/structured.jsonl | jq .
```

## Frontend
```bash
cd frontend

# Start dev server
npm run dev

# Run unit tests
npm test

# Run E2E tests
npm run test:e2e

# Build for production
npm run build
```

## Full Integration Test
```bash
# Terminal 1: Start backend
cd backend && uvicorn app.main:app --reload

# Terminal 2: Start frontend
cd frontend && npm run dev

# Terminal 3: Test flow
curl -X POST http://localhost:8000/api/jobs/fetch-all
# Wait for completion
curl http://localhost:8000/api/companies
# Open http://localhost:3000 in browser
```
