import logging
import json
from typing import Dict, Any, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiAnalyzer:
    """Service for analyzing SEC filings using Google Gemini"""

    def __init__(self, api_key: str):
        """Initialize the Gemini analyzer with API key"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def analyze(self, risk_factors: str, mda: str) -> Dict[str, Any]:
        """Analyze SEC filing content and return structured analysis"""
        prompt = self._build_prompt(risk_factors, mda)

        try:
            response = self.model.generate_content(prompt)
            return self._parse_response(response.text)
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            raise ValueError(f"GEMINI_API_ERROR: {str(e)}")

    def _build_prompt(self, risk_factors: str, mda: str) -> str:
        """Build the analysis prompt for Gemini"""
        return f"""Analyze this SEC 10-K filing and return a JSON response with the following structure:

{{
    "summary": "A 3-paragraph executive summary covering: 1) Company overview and business performance, 2) Key financial highlights and trends, 3) Major challenges and outlook",
    "risk_assessment": {{
        "operational": {{
            "score": <number 1-10>,
            "risks": ["risk1", "risk2", "risk3"]
        }},
        "financial": {{
            "score": <number 1-10>,
            "risks": ["risk1", "risk2", "risk3"]
        }},
        "regulatory": {{
            "score": <number 1-10>,
            "risks": ["risk1", "risk2", "risk3"]
        }},
        "strategic": {{
            "score": <number 1-10>,
            "risks": ["risk1", "risk2", "risk3"]
        }},
        "reputational": {{
            "score": <number 1-10>,
            "risks": ["risk1", "risk2", "risk3"]
        }}
    }}
}}

Risk Categories:
- Operational: Supply chain, cybersecurity, process failures, labor issues
- Financial: FX exposure, interest rates, liquidity, debt levels
- Regulatory: Compliance, environmental, data privacy, industry regulations
- Strategic: Competition, market disruption, concentration, M&A risks
- Reputational: ESG, climate, social responsibility, brand risks

Score Guide:
- 1-3: Low risk
- 4-6: Medium risk
- 7-10: High risk

IMPORTANT: Return ONLY valid JSON, no markdown formatting or extra text.

--- RISK FACTORS SECTION ---
{risk_factors[:15000]}

--- MD&A SECTION ---
{mda[:15000]}
"""

    def _parse_response(self, text: str) -> Dict[str, Any]:
        """Parse JSON from Gemini response"""
        try:
            # Try to extract JSON from the response
            # Handle cases where response might have markdown code blocks
            cleaned = text.strip()

            # Remove markdown code blocks if present
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]

            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            cleaned = cleaned.strip()

            # Find the JSON object
            start = cleaned.find('{')
            end = cleaned.rfind('}') + 1

            if start == -1 or end == 0:
                raise ValueError("No JSON object found in response")

            json_str = cleaned[start:end]
            result = json.loads(json_str)

            # Validate required fields
            if "summary" not in result:
                result["summary"] = "Analysis summary not available."

            if "risk_assessment" not in result:
                result["risk_assessment"] = self._default_risk_assessment()

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            logger.debug(f"Response text: {text[:500]}")
            raise ValueError(f"GEMINI_PARSE_ERROR: {str(e)}")

    def _default_risk_assessment(self) -> Dict[str, Any]:
        """Return default risk assessment structure"""
        default_category = {"score": 5, "risks": ["Unable to assess"]}
        return {
            "operational": default_category.copy(),
            "financial": default_category.copy(),
            "regulatory": default_category.copy(),
            "strategic": default_category.copy(),
            "reputational": default_category.copy()
        }
