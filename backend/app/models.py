from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    cik = Column(String(20), unique=True, nullable=False, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    sector = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    filings = relationship("Filing", back_populates="company")


class Filing(Base):
    __tablename__ = "filings"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    filing_type = Column(String(20), nullable=False)  # '10-K', '10-Q'
    filing_date = Column(Date, nullable=False)
    fiscal_year = Column(Integer)
    accession_number = Column(String(50), unique=True)
    filing_url = Column(Text)
    raw_content = Column(Text)  # Store extracted text
    status = Column(String(20), default="pending")  # pending, processing, completed, error
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    company = relationship("Company", back_populates="filings")
    analysis_result = relationship("AnalysisResult", back_populates="filing", uselist=False)
    risk_assessments = relationship("RiskAssessment", back_populates="filing")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    filing_id = Column(Integer, ForeignKey("filings.id"), nullable=False, unique=True)
    summary = Column(Text)  # Gemini-generated summary
    risk_factors_text = Column(Text)  # Extracted Item 1A
    mda_text = Column(Text)  # Extracted Item 7
    analysis_json = Column(Text)  # Full JSON analysis from Gemini
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    filing = relationship("Filing", back_populates="analysis_result")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    filing_id = Column(Integer, ForeignKey("filings.id"), nullable=False)
    category = Column(String(50), nullable=False)  # operational, financial, regulatory, strategic, reputational
    severity = Column(String(20), nullable=False)  # high, medium, low
    score = Column(Integer)  # 1-10
    description = Column(Text)
    key_risks = Column(Text)  # JSON array of specific risks
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    filing = relationship("Filing", back_populates="risk_assessments")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String(50), nullable=False)  # fetch, analyze
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    total_items = Column(Integer, default=0)
    completed_items = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
