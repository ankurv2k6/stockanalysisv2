"""
Unit tests for the Risk Calculator service.
"""

import pytest
from app.services.risk_calculator import RiskCalculator


class TestRiskCalculator:
    """Test suite for RiskCalculator class."""

    @pytest.fixture
    def calculator(self):
        """Create a RiskCalculator instance."""
        return RiskCalculator()

    def test_risk_categories_defined(self, calculator):
        """Should have all 5 risk categories defined."""
        expected_categories = ["operational", "financial", "regulatory", "strategic", "reputational"]
        assert calculator.RISK_CATEGORIES == expected_categories

    def test_calculate_overall_average(self, calculator):
        """Should calculate correct weighted average of scores."""
        scores = {
            "operational": 6,
            "financial": 4,
            "regulatory": 5,
            "strategic": 3,
            "reputational": 7
        }
        overall = calculator.calculate_overall(scores)
        expected = (6 + 4 + 5 + 3 + 7) / 5  # 5.0
        assert overall == expected

    def test_calculate_overall_empty_scores(self, calculator):
        """Should return 0 for empty scores."""
        overall = calculator.calculate_overall({})
        assert overall == 0

    def test_calculate_overall_partial_scores(self, calculator):
        """Should calculate average of provided scores only."""
        scores = {
            "operational": 8,
            "financial": 6
        }
        overall = calculator.calculate_overall(scores)
        assert overall == 7.0

    def test_get_severity_high(self, calculator):
        """Should return 'high' for scores >= 7."""
        assert calculator.get_severity(7) == "high"
        assert calculator.get_severity(8) == "high"
        assert calculator.get_severity(9) == "high"
        assert calculator.get_severity(10) == "high"

    def test_get_severity_medium(self, calculator):
        """Should return 'medium' for scores 4-6."""
        assert calculator.get_severity(4) == "medium"
        assert calculator.get_severity(5) == "medium"
        assert calculator.get_severity(6) == "medium"

    def test_get_severity_low(self, calculator):
        """Should return 'low' for scores < 4."""
        assert calculator.get_severity(1) == "low"
        assert calculator.get_severity(2) == "low"
        assert calculator.get_severity(3) == "low"

    def test_get_severity_boundary_values(self, calculator):
        """Should handle boundary values correctly."""
        assert calculator.get_severity(3.9) == "low"
        assert calculator.get_severity(4.0) == "medium"
        assert calculator.get_severity(6.9) == "medium"
        assert calculator.get_severity(7.0) == "high"


class TestRiskCalculatorDatabaseOperations:
    """Test suite for RiskCalculator database operations."""

    @pytest.fixture
    def calculator(self):
        """Create a RiskCalculator instance."""
        return RiskCalculator()

    def test_get_company_risk_scores_with_data(self, calculator, db_session, sample_analysis):
        """Should return risk scores for a company with analysis."""
        # sample_analysis fixture creates company, filing, and risk assessments
        company_id = sample_analysis.filing.company_id

        scores = calculator.get_company_risk_scores(db_session, company_id)

        assert scores is not None
        assert "overall" in scores
        assert "operational" in scores
        assert "financial" in scores
        assert "regulatory" in scores
        assert "strategic" in scores
        assert "reputational" in scores

    def test_get_company_risk_scores_no_data(self, calculator, db_session, sample_company):
        """Should return None for company without analysis."""
        scores = calculator.get_company_risk_scores(db_session, sample_company.id)
        assert scores is None

    def test_get_risk_summary_empty_db(self, calculator, db_session):
        """Should return zeros for empty database."""
        summary = calculator.get_risk_summary(db_session)

        assert summary["total_companies"] == 0
        assert summary["analyzed_companies"] == 0
        assert summary["high_risk_count"] == 0
        assert summary["medium_risk_count"] == 0
        assert summary["low_risk_count"] == 0

    def test_get_risk_summary_with_data(self, calculator, db_session, sample_analysis):
        """Should return correct summary with data."""
        summary = calculator.get_risk_summary(db_session)

        assert summary["total_companies"] == 1
        assert summary["analyzed_companies"] == 1
        # The sample analysis has medium overall score (avg of 5,4,6,3,4 = 4.4)
        assert summary["medium_risk_count"] == 1 or summary["low_risk_count"] == 1
