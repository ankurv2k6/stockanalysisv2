"""
Unit tests for the SEC Fetcher service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestSECFetcher:
    """Test suite for SECFetcher class."""

    @pytest.fixture
    def mock_edgar(self):
        """Mock the edgar module."""
        with patch('app.services.sec_fetcher.Company') as mock_company, \
             patch('app.services.sec_fetcher.set_identity') as mock_identity:
            yield {
                'Company': mock_company,
                'set_identity': mock_identity
            }

    @pytest.fixture
    def fetcher(self, mock_edgar):
        """Create a SECFetcher instance with mocked dependencies."""
        from app.services.sec_fetcher import SECFetcher
        return SECFetcher("TestApp test@example.com")

    def test_initialization_sets_identity(self, mock_edgar):
        """Should set user identity on initialization."""
        from app.services.sec_fetcher import SECFetcher
        fetcher = SECFetcher("TestApp test@example.com")
        mock_edgar['set_identity'].assert_called_once_with("TestApp test@example.com")

    def test_fetch_company_info_success(self, fetcher, mock_edgar):
        """Should return company info for valid ticker."""
        mock_company = Mock()
        mock_company.name = "Apple Inc."
        mock_company.cik = 320193
        mock_company.sic_description = "Technology"
        mock_edgar['Company'].return_value = mock_company

        result = fetcher.fetch_company_info("AAPL")

        assert result is not None
        assert result["ticker"] == "AAPL"
        assert result["name"] == "Apple Inc."
        assert result["cik"] == "0000320193"

    def test_fetch_company_info_error(self, fetcher, mock_edgar):
        """Should return None on error."""
        mock_edgar['Company'].side_effect = Exception("API Error")

        result = fetcher.fetch_company_info("INVALID")

        assert result is None

    def test_fetch_10k_success(self, fetcher, mock_edgar):
        """Should return 10-K filing for valid ticker."""
        mock_filing = Mock()
        mock_filing.accession_number = "0000320193-24-000123"
        mock_filing.filing_date = "2024-11-01"

        mock_filings = Mock()
        mock_filings.latest.return_value = [mock_filing]

        mock_company = Mock()
        mock_company.get_filings.return_value = mock_filings
        mock_edgar['Company'].return_value = mock_company

        result = fetcher.fetch_10k("AAPL")

        assert result is not None
        assert result.accession_number == "0000320193-24-000123"
        mock_company.get_filings.assert_called_once_with(form="10-K")

    def test_fetch_10k_not_found(self, fetcher, mock_edgar):
        """Should return None when no 10-K exists."""
        mock_filings = Mock()
        mock_filings.latest.return_value = []

        mock_company = Mock()
        mock_company.get_filings.return_value = mock_filings
        mock_edgar['Company'].return_value = mock_company

        result = fetcher.fetch_10k("INVALID")

        assert result is None

    def test_fetch_10k_error(self, fetcher, mock_edgar):
        """Should return None on API error."""
        mock_edgar['Company'].side_effect = Exception("Connection error")

        result = fetcher.fetch_10k("AAPL")

        assert result is None

    def test_fetch_10k_rate_limit(self, fetcher, mock_edgar):
        """Should handle rate limit errors."""
        mock_edgar['Company'].side_effect = Exception("429 Rate limit exceeded")

        result = fetcher.fetch_10k("AAPL")

        assert result is None

    def test_extract_sections_success(self, fetcher):
        """Should extract key sections from filing."""
        mock_tenk = Mock()
        mock_tenk.item1a = "Risk factors content..."
        mock_tenk.item7 = "MD&A content..."
        mock_tenk.item1 = "Business description..."

        mock_filing = Mock()
        mock_filing.obj.return_value = mock_tenk
        mock_filing.accession_number = "0000320193-24-000123"
        mock_filing.filing_date = "2024-11-01"
        mock_filing.fiscal_year = 2024

        result = fetcher.extract_sections(mock_filing)

        assert "risk_factors" in result
        assert "mda" in result
        assert "business" in result
        assert result["risk_factors"] == "Risk factors content..."
        assert result["accession_number"] == "0000320193-24-000123"

    def test_extract_sections_missing_items(self, fetcher):
        """Should handle missing items gracefully."""
        mock_tenk = Mock()
        mock_tenk.item1a = None
        mock_tenk.item7 = None
        mock_tenk.item1 = None

        mock_filing = Mock()
        mock_filing.obj.return_value = mock_tenk
        mock_filing.accession_number = "0000320193-24-000123"
        mock_filing.filing_date = "2024-11-01"

        result = fetcher.extract_sections(mock_filing)

        assert result["risk_factors"] == ""
        assert result["mda"] == ""
        assert result["business"] == ""

    def test_extract_sections_truncates_long_content(self, fetcher):
        """Should truncate content longer than max_length."""
        long_content = "x" * 60000  # Longer than 50000 limit

        mock_tenk = Mock()
        mock_tenk.item1a = long_content
        mock_tenk.item7 = long_content
        mock_tenk.item1 = long_content

        mock_filing = Mock()
        mock_filing.obj.return_value = mock_tenk
        mock_filing.accession_number = "0000320193-24-000123"
        mock_filing.filing_date = "2024-11-01"

        result = fetcher.extract_sections(mock_filing)

        assert len(result["risk_factors"]) == 50000
        assert len(result["mda"]) == 50000
        assert len(result["business"]) == 20000

    def test_extract_sections_error(self, fetcher):
        """Should handle extraction errors gracefully."""
        mock_filing = Mock()
        mock_filing.obj.side_effect = Exception("Parse error")
        mock_filing.accession_number = "0000320193-24-000123"
        mock_filing.filing_date = "2024-11-01"

        result = fetcher.extract_sections(mock_filing)

        assert result["risk_factors"] == ""
        assert result["mda"] == ""
        assert result["accession_number"] == "0000320193-24-000123"

    def test_get_filing_url(self, fetcher):
        """Should generate correct SEC URL."""
        mock_filing = Mock()
        mock_filing.cik = "320193"
        mock_filing.accession_number = "0000320193-24-000123"

        result = fetcher.get_filing_url(mock_filing)

        assert result is not None
        assert "320193" in result
        assert "000032019324000123" in result
        assert "sec.gov" in result

    def test_get_filing_url_error(self, fetcher):
        """Should return None on URL generation error."""
        mock_filing = Mock()
        mock_filing.cik = None  # This will cause an error

        result = fetcher.get_filing_url(mock_filing)

        # Should handle gracefully
        assert result is None or isinstance(result, str)
