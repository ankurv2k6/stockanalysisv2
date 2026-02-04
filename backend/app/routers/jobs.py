import json
import logging
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db, SessionLocal
from app.models import Company, Filing, AnalysisResult, RiskAssessment, Job
from app.schemas import JobResponse, JobStartResponse, RiskSummaryResponse
from app.services.sec_fetcher import SECFetcher
from app.services.gemini_analyzer import GeminiAnalyzer
from app.services.risk_calculator import RiskCalculator
from app.config import settings

router = APIRouter(prefix="/api/jobs", tags=["jobs"])
logger = logging.getLogger(__name__)


def load_sp100_tickers():
    """Load S&P 100 tickers from JSON file"""
    try:
        with open("data/sp100_companies.json", "r") as f:
            data = json.load(f)
            return data.get("companies", [])
    except Exception as e:
        logger.error(f"Failed to load S&P 100 tickers: {e}")
        return []


def fetch_all_task(job_id: int):
    """Background task to fetch all S&P 100 filings"""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()

        fetcher = SECFetcher(settings.SEC_USER_AGENT)
        companies_data = load_sp100_tickers()
        job.total_items = len(companies_data)
        db.commit()

        for i, company_data in enumerate(companies_data):
            try:
                ticker = company_data["ticker"]
                logger.info(f"Fetching {ticker} ({i+1}/{len(companies_data)})")

                # Check if company exists
                company = db.query(Company).filter(Company.ticker == ticker).first()

                if not company:
                    # Fetch company info from SEC
                    info = fetcher.fetch_company_info(ticker)
                    if info:
                        company = Company(
                            ticker=info["ticker"],
                            name=info["name"],
                            cik=info["cik"],
                            sector=company_data.get("sector", info.get("sector"))
                        )
                        db.add(company)
                        db.commit()
                        db.refresh(company)

                if company:
                    # Check if we already have a recent filing
                    existing_filing = (
                        db.query(Filing)
                        .filter(Filing.company_id == company.id, Filing.filing_type == "10-K")
                        .order_by(Filing.filing_date.desc())
                        .first()
                    )

                    # Fetch 10-K if we don't have one
                    if not existing_filing:
                        filing_data = fetcher.fetch_10k(ticker)
                        if filing_data:
                            sections = fetcher.extract_sections(filing_data)

                            filing = Filing(
                                company_id=company.id,
                                filing_type="10-K",
                                filing_date=datetime.strptime(sections["filing_date"], "%Y-%m-%d").date() if sections["filing_date"] else datetime.now().date(),
                                fiscal_year=sections.get("fiscal_year"),
                                accession_number=sections["accession_number"],
                                filing_url=fetcher.get_filing_url(filing_data),
                                raw_content=json.dumps(sections),
                                status="pending"
                            )
                            db.add(filing)
                            db.commit()

                job.completed_items = i + 1
                db.commit()

            except Exception as e:
                logger.error(f"Error fetching {company_data.get('ticker', 'unknown')}: {e}")
                continue

        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        logger.error(f"Fetch job failed: {e}")
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
    finally:
        db.close()


def analyze_all_task(job_id: int):
    """Background task to analyze all pending filings"""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()

        if not settings.GEMINI_API_KEY:
            job.status = "failed"
            job.error_message = "GEMINI_API_KEY not configured"
            db.commit()
            return

        analyzer = GeminiAnalyzer(settings.GEMINI_API_KEY)
        risk_calculator = RiskCalculator()

        # Get pending filings
        pending_filings = (
            db.query(Filing)
            .filter(Filing.status == "pending")
            .all()
        )

        job.total_items = len(pending_filings)
        db.commit()

        for i, filing in enumerate(pending_filings):
            try:
                logger.info(f"Analyzing filing {filing.id} ({i+1}/{len(pending_filings)})")

                # Parse raw content
                if not filing.raw_content:
                    continue

                sections = json.loads(filing.raw_content)
                risk_factors = sections.get("risk_factors", "")
                mda = sections.get("mda", "")

                if not risk_factors and not mda:
                    filing.status = "error"
                    db.commit()
                    continue

                # Analyze with Gemini
                filing.status = "processing"
                db.commit()

                analysis_result = analyzer.analyze(risk_factors, mda)

                # Save analysis result
                analysis = AnalysisResult(
                    filing_id=filing.id,
                    summary=analysis_result.get("summary", ""),
                    risk_factors_text=risk_factors[:50000],
                    mda_text=mda[:50000],
                    analysis_json=json.dumps(analysis_result)
                )
                db.add(analysis)

                # Save risk assessments
                risk_assessment = analysis_result.get("risk_assessment", {})
                for category, data in risk_assessment.items():
                    if category in risk_calculator.RISK_CATEGORIES:
                        score = data.get("score", 5)
                        ra = RiskAssessment(
                            filing_id=filing.id,
                            category=category,
                            severity=risk_calculator.get_severity(score),
                            score=score,
                            key_risks=json.dumps(data.get("risks", []))
                        )
                        db.add(ra)

                filing.status = "completed"
                job.completed_items = i + 1
                db.commit()

            except Exception as e:
                logger.error(f"Error analyzing filing {filing.id}: {e}")
                filing.status = "error"
                db.commit()
                continue

        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        logger.error(f"Analyze job failed: {e}")
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
    finally:
        db.close()


@router.post("/fetch-all", response_model=JobStartResponse)
async def start_fetch_all(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Start background job to fetch all S&P 100 filings"""
    # Check if there's already a running fetch job
    running_job = db.query(Job).filter(Job.job_type == "fetch", Job.status == "running").first()
    if running_job:
        raise HTTPException(status_code=400, detail="A fetch job is already running")

    # Create new job
    job = Job(job_type="fetch", status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)

    # Start background task
    background_tasks.add_task(fetch_all_task, job.id)

    return JobStartResponse(
        job_id=job.id,
        status="started",
        message="Fetch job started. Use /api/jobs/status to check progress."
    )


@router.post("/analyze-all", response_model=JobStartResponse)
async def start_analyze_all(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Start background job to analyze all pending filings"""
    # Check if there's already a running analyze job
    running_job = db.query(Job).filter(Job.job_type == "analyze", Job.status == "running").first()
    if running_job:
        raise HTTPException(status_code=400, detail="An analyze job is already running")

    # Create new job
    job = Job(job_type="analyze", status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)

    # Start background task
    background_tasks.add_task(analyze_all_task, job.id)

    return JobStartResponse(
        job_id=job.id,
        status="started",
        message="Analyze job started. Use /api/jobs/status to check progress."
    )


@router.get("/status", response_model=Optional[JobResponse])
async def get_job_status(job_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get status of a specific job or the latest running job"""
    if job_id:
        job = db.query(Job).filter(Job.id == job_id).first()
    else:
        # Get the most recent job
        job = db.query(Job).order_by(Job.created_at.desc()).first()

    if not job:
        return None

    return JobResponse(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        total_items=job.total_items,
        completed_items=job.completed_items,
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at
    )


@router.get("/history", response_model=list[JobResponse])
async def get_job_history(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent job history"""
    jobs = db.query(Job).order_by(Job.created_at.desc()).limit(limit).all()

    return [JobResponse(
        id=j.id,
        job_type=j.job_type,
        status=j.status,
        total_items=j.total_items,
        completed_items=j.completed_items,
        error_message=j.error_message,
        started_at=j.started_at,
        completed_at=j.completed_at
    ) for j in jobs]


@router.get("/risk-summary", response_model=RiskSummaryResponse)
async def get_risk_summary(db: Session = Depends(get_db)):
    """Get aggregated risk summary across all analyzed companies"""
    calculator = RiskCalculator()
    summary = calculator.get_risk_summary(db)

    return RiskSummaryResponse(
        total_companies=summary["total_companies"],
        analyzed_companies=summary["analyzed_companies"],
        high_risk_count=summary["high_risk_count"],
        medium_risk_count=summary["medium_risk_count"],
        low_risk_count=summary["low_risk_count"],
        average_risk_score=summary["average_risk_score"],
        risk_by_category=summary["risk_by_category"]
    )
