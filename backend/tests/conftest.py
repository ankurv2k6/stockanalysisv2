"""
Pytest configuration and fixtures for testing.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.models import Company, Filing, AnalysisResult, RiskAssessment, Job


# Test database URL - use in-memory SQLite
TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine):
    """Create a new database session for each test."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        # Clean up all data after each test
        session.query(RiskAssessment).delete()
        session.query(AnalysisResult).delete()
        session.query(Filing).delete()
        session.query(Company).delete()
        session.query(Job).delete()
        session.commit()
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_company(db_session):
    """Create a sample company for testing."""
    company = Company(
        ticker="AAPL",
        name="Apple Inc.",
        cik="0000320193",
        sector="Technology"
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest.fixture
def sample_filing(db_session, sample_company):
    """Create a sample filing for testing."""
    from datetime import date
    import json

    filing = Filing(
        company_id=sample_company.id,
        filing_type="10-K",
        filing_date=date(2024, 11, 1),
        fiscal_year=2024,
        accession_number="0000320193-24-000123",
        raw_content=json.dumps({
            "risk_factors": "Sample risk factors text...",
            "mda": "Sample MD&A text...",
            "business": "Sample business description..."
        }),
        status="pending"
    )
    db_session.add(filing)
    db_session.commit()
    db_session.refresh(filing)
    return filing


@pytest.fixture
def sample_analysis(db_session, sample_filing):
    """Create a sample analysis result for testing."""
    import json

    analysis = AnalysisResult(
        filing_id=sample_filing.id,
        summary="This is a test summary of the 10-K filing.",
        risk_factors_text="Sample risk factors...",
        mda_text="Sample MD&A...",
        analysis_json=json.dumps({
            "summary": "Test summary",
            "risk_assessment": {
                "operational": {"score": 5, "risks": ["Risk 1"]},
                "financial": {"score": 4, "risks": ["Risk 2"]},
                "regulatory": {"score": 6, "risks": ["Risk 3"]},
                "strategic": {"score": 3, "risks": ["Risk 4"]},
                "reputational": {"score": 4, "risks": ["Risk 5"]}
            }
        })
    )
    db_session.add(analysis)

    # Add risk assessments
    for category, score in [
        ("operational", 5),
        ("financial", 4),
        ("regulatory", 6),
        ("strategic", 3),
        ("reputational", 4)
    ]:
        ra = RiskAssessment(
            filing_id=sample_filing.id,
            category=category,
            severity="medium" if 4 <= score <= 6 else ("high" if score > 6 else "low"),
            score=score,
            key_risks=json.dumps([f"Sample {category} risk"])
        )
        db_session.add(ra)

    sample_filing.status = "completed"
    db_session.commit()
    db_session.refresh(analysis)
    return analysis


@pytest.fixture
def sample_gemini_response():
    """Sample Gemini API response for mocking."""
    return {
        "summary": "Apple Inc. reported strong fiscal 2024 results with revenue of $383B. Key growth areas include Services and wearables. The company faces supply chain risks in Asia and regulatory challenges in Europe.",
        "risk_assessment": {
            "operational": {
                "score": 6,
                "risks": ["Supply chain concentration in Asia", "Manufacturing delays", "Labor disputes"]
            },
            "financial": {
                "score": 4,
                "risks": ["Foreign exchange exposure", "Interest rate sensitivity", "Revenue concentration"]
            },
            "regulatory": {
                "score": 7,
                "risks": ["EU antitrust investigations", "Data privacy regulations", "App Store policies"]
            },
            "strategic": {
                "score": 5,
                "risks": ["Competition in smartphone market", "AI technology race", "Market saturation"]
            },
            "reputational": {
                "score": 4,
                "risks": ["Environmental concerns", "Labor practices", "Privacy controversies"]
            }
        }
    }
