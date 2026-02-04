"""
Structured Logging Configuration

Provides dual-format logging:
1. Human-readable console/file output
2. Machine-parseable JSON for automation (Claude Code compatible)
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Standard error codes for automated detection
ERROR_CODES = {
    "SEC_RATE_LIMIT": {
        "description": "SEC API rate limit exceeded",
        "recoverable": True,
        "suggested_fix": "Wait 60 seconds and retry"
    },
    "SEC_FILING_NOT_FOUND": {
        "description": "No 10-K filing found for ticker",
        "recoverable": True,
        "suggested_fix": "Skip company and continue with next"
    },
    "SEC_PARSE_ERROR": {
        "description": "Failed to parse SEC filing",
        "recoverable": True,
        "suggested_fix": "Check edgartools version or skip filing"
    },
    "SEC_CONNECTION_ERROR": {
        "description": "Failed to connect to SEC EDGAR",
        "recoverable": True,
        "suggested_fix": "Check network connection and retry"
    },
    "GEMINI_API_ERROR": {
        "description": "Gemini API returned error",
        "recoverable": True,
        "suggested_fix": "Check API key validity and quota"
    },
    "GEMINI_RATE_LIMIT": {
        "description": "Gemini API rate limit exceeded",
        "recoverable": True,
        "suggested_fix": "Implement exponential backoff and retry"
    },
    "GEMINI_PARSE_ERROR": {
        "description": "Failed to parse Gemini JSON response",
        "recoverable": True,
        "suggested_fix": "Retry with stricter prompt or adjust parsing"
    },
    "DB_CONNECTION_ERROR": {
        "description": "Database connection failed",
        "recoverable": False,
        "suggested_fix": "Check DATABASE_URL and file permissions"
    },
    "DB_INTEGRITY_ERROR": {
        "description": "Database constraint violation",
        "recoverable": True,
        "suggested_fix": "Check for duplicate data before insert"
    },
    "ANALYSIS_INCOMPLETE": {
        "description": "Analysis missing required fields",
        "recoverable": True,
        "suggested_fix": "Re-run Gemini analysis for this filing"
    },
}


class StructuredLogger:
    """
    Dual-format logger: human readable + JSON for automation.

    Usage:
        log = StructuredLogger("sec_fetcher")
        log.info("Fetching filing", ticker="AAPL", filing_type="10-K")
        log.error("API failed", error_code="SEC_RATE_LIMIT", retry_after=60)
    """

    def __init__(self, name: str, log_dir: str = "logs"):
        self.component = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Set up Python logger
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            self.logger.setLevel(logging.DEBUG)

            # Console handler (human readable)
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_format = logging.Formatter(
                '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_format)
            self.logger.addHandler(console_handler)

            # File handler (human readable)
            file_handler = logging.FileHandler(self.log_dir / "app.log")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(console_format)
            self.logger.addHandler(file_handler)

    def _write_json_log(self, entry: dict):
        """Append JSON log entry to structured log file."""
        json_path = self.log_dir / "structured.jsonl"
        with open(json_path, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def _create_log_entry(
        self,
        level: str,
        message: str,
        error_code: Optional[str] = None,
        **context
    ) -> dict:
        """Create structured log entry."""
        timestamp = datetime.utcnow().isoformat() + "Z"

        entry = {
            "timestamp": timestamp,
            "level": level,
            "component": self.component,
            "message": message,
            "context": context if context else None,
        }

        # Add error metadata if error_code provided
        if error_code and error_code in ERROR_CODES:
            error_info = ERROR_CODES[error_code]
            entry["error_code"] = error_code
            entry["recoverable"] = error_info["recoverable"]
            entry["suggested_fix"] = error_info["suggested_fix"]
        elif error_code:
            entry["error_code"] = error_code
            entry["recoverable"] = True
            entry["suggested_fix"] = None

        return entry

    def _log(
        self,
        level: str,
        message: str,
        error_code: Optional[str] = None,
        **context
    ):
        """Internal logging method."""
        entry = self._create_log_entry(level, message, error_code, **context)

        # Human-readable log message
        human_msg = message
        if context:
            context_str = " | ".join(f"{k}={v}" for k, v in context.items())
            human_msg = f"{message} | {context_str}"

        # Log to Python logger
        log_method = getattr(self.logger, level.lower())
        log_method(human_msg)

        # Write JSON log
        self._write_json_log(entry)

        return entry

    def debug(self, message: str, **context):
        """Log debug message."""
        return self._log("DEBUG", message, **context)

    def info(self, message: str, **context):
        """Log info message."""
        return self._log("INFO", message, **context)

    def warning(self, message: str, error_code: Optional[str] = None, **context):
        """Log warning message."""
        return self._log("WARNING", message, error_code, **context)

    def error(
        self,
        message: str,
        error_code: Optional[str] = None,
        exception: Optional[Exception] = None,
        **context
    ):
        """Log error message with optional error code and exception."""
        if exception:
            context["exception_type"] = type(exception).__name__
            context["exception_message"] = str(exception)
        return self._log("ERROR", message, error_code, **context)

    def critical(self, message: str, error_code: Optional[str] = None, **context):
        """Log critical message."""
        return self._log("CRITICAL", message, error_code, **context)


def get_logger(name: str) -> StructuredLogger:
    """Factory function to get a structured logger."""
    return StructuredLogger(name)


# Create module-level loggers for common components
sec_logger = get_logger("sec_fetcher")
gemini_logger = get_logger("gemini_analyzer")
db_logger = get_logger("database")
api_logger = get_logger("api")
job_logger = get_logger("jobs")
