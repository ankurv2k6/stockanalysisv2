from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import Filing, AnalysisResult, RiskAssessment
from app.schemas import FilingResponse, AnalysisResponse

router = APIRouter(prefix="/api/filings", tags=["filings"])


@router.get("", response_model=List[FilingResponse])
async def list_filings(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all filings with optional status filter"""
    query = db.query(Filing)

    if status:
        query = query.filter(Filing.status == status)

    filings = query.order_by(Filing.filing_date.desc()).offset(skip).limit(limit).all()

    return [FilingResponse(
        id=f.id,
        company_id=f.company_id,
        filing_type=f.filing_type,
        filing_date=f.filing_date,
        fiscal_year=f.fiscal_year,
        accession_number=f.accession_number,
        status=f.status,
        created_at=f.created_at
    ) for f in filings]


@router.get("/{filing_id}", response_model=FilingResponse)
async def get_filing(filing_id: int, db: Session = Depends(get_db)):
    """Get filing details"""
    filing = db.query(Filing).filter(Filing.id == filing_id).first()

    if not filing:
        raise HTTPException(status_code=404, detail=f"Filing with id {filing_id} not found")

    return FilingResponse(
        id=filing.id,
        company_id=filing.company_id,
        filing_type=filing.filing_type,
        filing_date=filing.filing_date,
        fiscal_year=filing.fiscal_year,
        accession_number=filing.accession_number,
        status=filing.status,
        created_at=filing.created_at
    )


@router.get("/{filing_id}/analysis")
async def get_filing_analysis(filing_id: int, db: Session = Depends(get_db)):
    """Get analysis results for a specific filing"""
    filing = db.query(Filing).filter(Filing.id == filing_id).first()

    if not filing:
        raise HTTPException(status_code=404, detail=f"Filing with id {filing_id} not found")

    analysis = db.query(AnalysisResult).filter(AnalysisResult.filing_id == filing_id).first()

    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analysis not found for filing {filing_id}")

    # Get risk assessments
    risk_assessments = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.filing_id == filing_id)
        .all()
    )

    import json
    risk_assessment_detail = {}
    for ra in risk_assessments:
        risks = json.loads(ra.key_risks) if ra.key_risks else []
        risk_assessment_detail[ra.category] = {
            "score": ra.score,
            "severity": ra.severity,
            "risks": risks
        }

    return {
        "id": analysis.id,
        "filing_id": analysis.filing_id,
        "summary": analysis.summary,
        "risk_factors_text": analysis.risk_factors_text[:1000] + "..." if analysis.risk_factors_text and len(analysis.risk_factors_text) > 1000 else analysis.risk_factors_text,
        "mda_text": analysis.mda_text[:1000] + "..." if analysis.mda_text and len(analysis.mda_text) > 1000 else analysis.mda_text,
        "risk_assessment": risk_assessment_detail,
        "created_at": analysis.created_at
    }
