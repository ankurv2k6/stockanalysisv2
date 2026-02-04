from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List


# Company schemas
class CompanyBase(BaseModel):
    ticker: str
    name: str
    cik: str
    sector: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class RiskScores(BaseModel):
    operational: Optional[int] = None
    financial: Optional[int] = None
    regulatory: Optional[int] = None
    strategic: Optional[int] = None
    reputational: Optional[int] = None
    overall: Optional[float] = None


class CompanyResponse(CompanyBase):
    id: int
    created_at: datetime
    latest_filing_date: Optional[date] = None
    risk_scores: Optional[RiskScores] = None

    class Config:
        from_attributes = True


class CompanyListResponse(BaseModel):
    companies: List[CompanyResponse]
    total: int


# Filing schemas
class FilingBase(BaseModel):
    filing_type: str
    filing_date: date
    fiscal_year: Optional[int] = None
    accession_number: Optional[str] = None


class FilingResponse(FilingBase):
    id: int
    company_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# Analysis schemas
class RiskCategoryDetail(BaseModel):
    score: int
    risks: List[str]


class RiskAssessmentDetail(BaseModel):
    operational: RiskCategoryDetail
    financial: RiskCategoryDetail
    regulatory: RiskCategoryDetail
    strategic: RiskCategoryDetail
    reputational: RiskCategoryDetail


class AnalysisResponse(BaseModel):
    id: int
    filing_id: int
    summary: Optional[str] = None
    risk_assessment: Optional[RiskAssessmentDetail] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Company detail with analysis
class CompanyDetailResponse(CompanyBase):
    id: int
    created_at: datetime
    filings: List[FilingResponse]
    latest_analysis: Optional[AnalysisResponse] = None
    risk_scores: Optional[RiskScores] = None

    class Config:
        from_attributes = True


# Job schemas
class JobResponse(BaseModel):
    id: int
    job_type: str
    status: str
    total_items: int
    completed_items: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobStartResponse(BaseModel):
    job_id: int
    status: str
    message: str


# Risk summary schemas
class RiskSummaryResponse(BaseModel):
    total_companies: int
    analyzed_companies: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    average_risk_score: Optional[float] = None
    risk_by_category: RiskScores
