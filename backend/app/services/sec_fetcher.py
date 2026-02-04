from typing import Optional, Dict, Any
from edgar import Company, set_identity

from app.logging_config import sec_logger as logger


class SECFetcher:
    """Service for fetching SEC filings using edgartools"""

    def __init__(self, user_agent: str):
        """Initialize the SEC fetcher with user agent for identification"""
        set_identity(user_agent)
        self.user_agent = user_agent
        logger.info("SEC Fetcher initialized", user_agent=user_agent)

    def fetch_company_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetch company information from SEC EDGAR"""
        try:
            logger.debug("Fetching company info", ticker=ticker)
            company = Company(ticker)
            result = {
                "ticker": ticker.upper(),
                "name": company.name,
                "cik": str(company.cik).zfill(10),
                "sector": getattr(company, 'sic_description', None)
            }
            logger.info("Company info fetched", ticker=ticker, name=company.name)
            return result
        except Exception as e:
            logger.error(
                "Failed to fetch company info",
                error_code="SEC_CONNECTION_ERROR",
                exception=e,
                ticker=ticker
            )
            return None

    def fetch_10k(self, ticker: str) -> Optional[Any]:
        """Fetch the latest 10-K filing for a company"""
        try:
            logger.debug("Fetching 10-K filing", ticker=ticker)
            company = Company(ticker)
            filings = company.get_filings(form="10-K").latest(1)
            if filings and len(filings) > 0:
                filing = filings[0]
                logger.info(
                    "10-K filing fetched",
                    ticker=ticker,
                    accession_number=filing.accession_number,
                    filing_date=str(filing.filing_date)
                )
                return filing
            logger.warning(
                "No 10-K filing found",
                error_code="SEC_FILING_NOT_FOUND",
                ticker=ticker
            )
            return None
        except Exception as e:
            if "rate" in str(e).lower() or "429" in str(e):
                logger.error(
                    "SEC rate limit exceeded",
                    error_code="SEC_RATE_LIMIT",
                    exception=e,
                    ticker=ticker
                )
            else:
                logger.error(
                    "Failed to fetch 10-K",
                    error_code="SEC_CONNECTION_ERROR",
                    exception=e,
                    ticker=ticker
                )
            return None

    def extract_sections(self, filing: Any) -> Dict[str, str]:
        """Extract key sections from a 10-K filing"""
        try:
            logger.debug("Extracting sections", accession_number=filing.accession_number)
            tenk = filing.obj()
            result = {
                "risk_factors": self._safe_extract(tenk, "item1a", 50000),
                "mda": self._safe_extract(tenk, "item7", 50000),
                "business": self._safe_extract(tenk, "item1", 20000),
                "accession_number": filing.accession_number,
                "filing_date": str(filing.filing_date),
                "fiscal_year": getattr(filing, 'fiscal_year', None)
            }
            logger.info(
                "Sections extracted",
                accession_number=filing.accession_number,
                risk_factors_len=len(result["risk_factors"]),
                mda_len=len(result["mda"])
            )
            return result
        except Exception as e:
            logger.error(
                "Failed to extract sections",
                error_code="SEC_PARSE_ERROR",
                exception=e,
                accession_number=getattr(filing, 'accession_number', 'unknown')
            )
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
