import logging
from typing import Optional, Dict, Any
from edgar import Company, set_identity

logger = logging.getLogger(__name__)


class SECFetcher:
    """Service for fetching SEC filings using edgartools"""

    def __init__(self, user_agent: str):
        """Initialize the SEC fetcher with user agent for identification"""
        set_identity(user_agent)
        self.user_agent = user_agent

    def fetch_company_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetch company information from SEC EDGAR"""
        try:
            company = Company(ticker)
            return {
                "ticker": ticker.upper(),
                "name": company.name,
                "cik": str(company.cik).zfill(10),
                "sector": getattr(company, 'sic_description', None)
            }
        except Exception as e:
            logger.error(f"Failed to fetch company info for {ticker}: {e}")
            return None

    def fetch_10k(self, ticker: str) -> Optional[Any]:
        """Fetch the latest 10-K filing for a company"""
        try:
            company = Company(ticker)
            filings = company.get_filings(form="10-K").latest(1)
            if filings and len(filings) > 0:
                return filings[0]
            return None
        except Exception as e:
            logger.error(f"Failed to fetch 10-K for {ticker}: {e}")
            return None

    def extract_sections(self, filing: Any) -> Dict[str, str]:
        """Extract key sections from a 10-K filing"""
        try:
            tenk = filing.obj()
            return {
                "risk_factors": self._safe_extract(tenk, "item1a", 50000),
                "mda": self._safe_extract(tenk, "item7", 50000),
                "business": self._safe_extract(tenk, "item1", 20000),
                "accession_number": filing.accession_number,
                "filing_date": str(filing.filing_date),
                "fiscal_year": getattr(filing, 'fiscal_year', None)
            }
        except Exception as e:
            logger.error(f"Failed to extract sections: {e}")
            return {
                "risk_factors": "",
                "mda": "",
                "business": "",
                "accession_number": getattr(filing, 'accession_number', None),
                "filing_date": str(getattr(filing, 'filing_date', '')),
                "fiscal_year": None
            }

    def _safe_extract(self, tenk: Any, item_name: str, max_length: int) -> str:
        """Safely extract an item from the 10-K, handling missing items"""
        try:
            item = getattr(tenk, item_name, None)
            if item is None:
                return ""
            text = str(item)
            return text[:max_length] if len(text) > max_length else text
        except Exception:
            return ""

    def get_filing_url(self, filing: Any) -> Optional[str]:
        """Get the SEC EDGAR URL for a filing"""
        try:
            return f"https://www.sec.gov/Archives/edgar/data/{filing.cik}/{filing.accession_number.replace('-', '')}"
        except Exception:
            return None
