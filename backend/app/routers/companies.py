from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import Company, Filing, RiskAssessment, AnalysisResult
from app.schemas import CompanyResponse, CompanyDetailResponse, CompanyListResponse, RiskScores, FilingResponse
from app.services.risk_calculator import RiskCalculator

router = APIRouter(prefix="/api/companies", tags=["companies"])
risk_calculator = RiskCalculator()


@router.get("", response_model=CompanyListResponse)
async def list_companies(
    skip: int = 0,
    limit: int = 100,
    sector: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all companies with their latest risk scores"""
    query = db.query(Company)

    if sector:
        query = query.filter(Company.sector == sector)

    total = query.count()
    companies = query.offset(skip).limit(limit).all()

    result = []
    for company in companies:
        # Get latest filing date
        latest_filing = (
            db.query(Filing)
            .filter(Filing.company_id == company.id)
            .order_by(Filing.filing_date.desc())
            .first()
        )

        # Get risk scores
        risk_scores = risk_calculator.get_company_risk_scores(db, company.id)

        company_data = CompanyResponse(
            id=company.id,
            ticker=company.ticker,
            name=company.name,
            cik=company.cik,
            sector=company.sector,
            created_at=company.created_at,
            latest_filing_date=latest_filing.filing_date if latest_filing else None,
            risk_scores=RiskScores(**risk_scores) if risk_scores else None
        )
        result.append(company_data)

    return CompanyListResponse(companies=result, total=total)


@router.get("/{ticker}", response_model=CompanyDetailResponse)
async def get_company(ticker: str, db: Session = Depends(get_db)):
    """Get detailed company information including filings and analysis"""
    company = db.query(Company).filter(Company.ticker == ticker.upper()).first()

    if not company:
        raise HTTPException(status_code=404, detail=f"Company with ticker {ticker} not found")

    # Get all filings
    filings = (
        db.query(Filing)
        .filter(Filing.company_id == company.id)
        .order_by(Filing.filing_date.desc())
        .all()
    )

    # Get latest analysis
    latest_analysis = None
    if filings:
        latest_completed = next((f for f in filings if f.status == "completed"), None)
        if latest_completed and latest_completed.analysis_result:
            analysis = latest_completed.analysis_result
            # Get risk assessments
            risk_assessments = (
                db.query(RiskAssessment)
                .filter(RiskAssessment.filing_id == latest_completed.id)
                .all()
            )

            risk_assessment_detail = {}
            for ra in risk_assessments:
                import json
                risks = json.loads(ra.key_risks) if ra.key_risks else []
                risk_assessment_detail[ra.category] = {
                    "score": ra.score,
                    "risks": risks
                }

            latest_analysis = {
                "id": analysis.id,
                "filing_id": analysis.filing_id,
                "summary": analysis.summary,
                "risk_assessment": risk_assessment_detail if risk_assessment_detail else None,
                "created_at": analysis.created_at
            }

    # Get risk scores
    risk_scores = risk_calculator.get_company_risk_scores(db, company.id)

    return CompanyDetailResponse(
        id=company.id,
        ticker=company.ticker,
        name=company.name,
        cik=company.cik,
        sector=company.sector,
        created_at=company.created_at,
        filings=[FilingResponse(
            id=f.id,
            company_id=f.company_id,
            filing_type=f.filing_type,
            filing_date=f.filing_date,
            fiscal_year=f.fiscal_year,
            accession_number=f.accession_number,
            status=f.status,
            created_at=f.created_at
        ) for f in filings],
        latest_analysis=latest_analysis,
        risk_scores=RiskScores(**risk_scores) if risk_scores else None
    )


@router.get("/sectors/list")
async def list_sectors(db: Session = Depends(get_db)):
    """List all unique sectors"""
    sectors = db.query(Company.sector).distinct().filter(Company.sector.isnot(None)).all()
    return {"sectors": [s[0] for s in sectors]}
