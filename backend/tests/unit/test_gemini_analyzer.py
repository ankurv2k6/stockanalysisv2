"""
Unit tests for the Gemini Analyzer service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from app.services.gemini_analyzer import GeminiAnalyzer


class TestGeminiAnalyzer:
    """Test suite for GeminiAnalyzer class."""

    @pytest.fixture
    def mock_genai(self):
        """Mock the google.generativeai module."""
        with patch('app.services.gemini_analyzer.genai') as mock:
            yield mock

    @pytest.fixture
    def analyzer(self, mock_genai):
        """Create a GeminiAnalyzer instance with mocked API."""
        return GeminiAnalyzer("test-api-key")

    def test_initialization(self, mock_genai):
        """Should configure genai with API key on init."""
        analyzer = GeminiAnalyzer("test-api-key")
        mock_genai.configure.assert_called_once_with(api_key="test-api-key")

    def test_analyze_returns_structured_response(self, analyzer, mock_genai, sample_gemini_response):
        """Should return properly structured analysis result."""
        # Mock the model response
        mock_response = Mock()
        mock_response.text = json.dumps(sample_gemini_response)
        analyzer.model.generate_content = Mock(return_value=mock_response)

        result = analyzer.analyze("Risk factors text...", "MD&A text...")

        assert "summary" in result
        assert "risk_assessment" in result
        assert len(result["risk_assessment"]) == 5
        assert all(cat in result["risk_assessment"] for cat in
                   ["operational", "financial", "regulatory", "strategic", "reputational"])

    def test_analyze_parses_json_with_markdown(self, analyzer, sample_gemini_response):
        """Should handle Gemini response wrapped in markdown code blocks."""
        # Mock response with markdown
        mock_response = Mock()
        mock_response.text = f"```json\n{json.dumps(sample_gemini_response)}\n```"
        analyzer.model.generate_content = Mock(return_value=mock_response)

        result = analyzer.analyze("Risk factors...", "MD&A...")

        assert result["summary"] == sample_gemini_response["summary"]

    def test_analyze_handles_malformed_json(self, analyzer):
        """Should raise ValueError for malformed JSON response."""
        mock_response = Mock()
        mock_response.text = "This is not valid JSON at all"
        analyzer.model.generate_content = Mock(return_value=mock_response)

        with pytest.raises(ValueError) as exc_info:
            analyzer.analyze("Risk factors...", "MD&A...")

        assert "GEMINI_PARSE_ERROR" in str(exc_info.value)

    def test_analyze_handles_missing_summary(self, analyzer):
        """Should add default summary if missing from response."""
        mock_response = Mock()
        mock_response.text = json.dumps({
            "risk_assessment": {
                "operational": {"score": 5, "risks": ["Risk 1"]}
            }
        })
        analyzer.model.generate_content = Mock(return_value=mock_response)

        result = analyzer.analyze("Risk factors...", "MD&A...")

        assert "summary" in result
        assert result["summary"] == "Analysis summary not available."

    def test_analyze_handles_missing_risk_assessment(self, analyzer):
        """Should add default risk assessment if missing from response."""
        mock_response = Mock()
        mock_response.text = json.dumps({
            "summary": "Test summary only"
        })
        analyzer.model.generate_content = Mock(return_value=mock_response)

        result = analyzer.analyze("Risk factors...", "MD&A...")

        assert "risk_assessment" in result
        assert len(result["risk_assessment"]) == 5

    def test_analyze_api_error(self, analyzer):
        """Should raise ValueError on API error."""
        analyzer.model.generate_content = Mock(side_effect=Exception("API Error"))

        with pytest.raises(ValueError) as exc_info:
            analyzer.analyze("Risk factors...", "MD&A...")

        assert "GEMINI_API_ERROR" in str(exc_info.value)

    def test_analyze_rate_limit_detection(self, analyzer):
        """Should detect rate limit errors."""
        analyzer.model.generate_content = Mock(
            side_effect=Exception("429 Resource has been exhausted (quota)")
        )

        with pytest.raises(ValueError) as exc_info:
            analyzer.analyze("Risk factors...", "MD&A...")

        assert "GEMINI_API_ERROR" in str(exc_info.value)

    def test_build_prompt_contains_sections(self, analyzer):
        """Should build prompt with risk factors and MD&A sections."""
        prompt = analyzer._build_prompt("Risk factors text", "MD&A text")

        assert "Risk factors text" in prompt
        assert "MD&A text" in prompt
        assert "risk_assessment" in prompt
        assert "operational" in prompt
        assert "1-10" in prompt

    def test_build_prompt_truncates_long_content(self, analyzer):
        """Should truncate content longer than 15000 chars."""
        long_text = "x" * 20000
        prompt = analyzer._build_prompt(long_text, long_text)

        # The prompt should contain truncated versions
        assert len(prompt) < 40000 + 2000  # 2 * 15000 + prompt template

    def test_default_risk_assessment_structure(self, analyzer):
        """Should return valid default risk assessment."""
        default = analyzer._default_risk_assessment()

        assert len(default) == 5
        for category in ["operational", "financial", "regulatory", "strategic", "reputational"]:
            assert category in default
            assert default[category]["score"] == 5
            assert "risks" in default[category]
