from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import RiskAssessment, Filing, Company


class RiskCalculator:
    """Service for calculating and aggregating risk scores"""

    RISK_CATEGORIES = ["operational", "financial", "regulatory", "strategic", "reputational"]

    def calculate_overall(self, scores: Dict[str, int]) -> float:
        """Calculate weighted average of category scores"""
        valid_scores = [v for v in scores.values() if v is not None]
        if not valid_scores:
            return 0.0
        return round(sum(valid_scores) / len(valid_scores), 1)

    def get_severity(self, score: int) -> str:
        """Categorize a score into severity level"""
        if score >= 7:
            return "high"
        elif score >= 4:
            return "medium"
        else:
            return "low"

    def get_company_risk_scores(self, db: Session, company_id: int) -> Optional[Dict[str, int]]:
        """Get the latest risk scores for a company"""
        # Get the latest filing for the company
        latest_filing = (
            db.query(Filing)
            .filter(Filing.company_id == company_id, Filing.status == "completed")
            .order_by(Filing.filing_date.desc())
            .first()
        )

        if not latest_filing:
            return None

        # Get risk assessments for this filing
        assessments = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.filing_id == latest_filing.id)
            .all()
        )

        scores = {}
        for assessment in assessments:
            scores[assessment.category] = assessment.score

        if scores:
            scores["overall"] = self.calculate_overall(scores)

        return scores if scores else None

    def get_risk_summary(self, db: Session) -> Dict:
        """Get aggregated risk summary across all companies"""
        # Count companies
        total_companies = db.query(Company).count()

        # Count analyzed companies (those with completed filings)
        analyzed_companies = (
            db.query(Company)
            .join(Filing)
            .filter(Filing.status == "completed")
            .distinct()
            .count()
        )

        # Get all risk assessments for completed filings
        assessments = (
            db.query(RiskAssessment)
            .join(Filing)
            .filter(Filing.status == "completed")
            .all()
        )

        # Calculate averages by category
        category_scores = {cat: [] for cat in self.RISK_CATEGORIES}
        filing_overall_scores = {}

        for assessment in assessments:
            category_scores[assessment.category].append(assessment.score)

            if assessment.filing_id not in filing_overall_scores:
                filing_overall_scores[assessment.filing_id] = []
            filing_overall_scores[assessment.filing_id].append(assessment.score)

        # Calculate average by category
        risk_by_category = {}
        for cat, scores in category_scores.items():
            risk_by_category[cat] = round(sum(scores) / len(scores), 1) if scores else None

        # Calculate overall scores per filing and count severity levels
        high_risk = 0
        medium_risk = 0
        low_risk = 0
        all_overall_scores = []

        for filing_id, scores in filing_overall_scores.items():
            overall = sum(scores) / len(scores)
            all_overall_scores.append(overall)

            severity = self.get_severity(round(overall))
            if severity == "high":
                high_risk += 1
            elif severity == "medium":
                medium_risk += 1
            else:
                low_risk += 1

        average_risk_score = round(sum(all_overall_scores) / len(all_overall_scores), 1) if all_overall_scores else None

        return {
            "total_companies": total_companies,
            "analyzed_companies": analyzed_companies,
            "high_risk_count": high_risk,
            "medium_risk_count": medium_risk,
            "low_risk_count": low_risk,
            "average_risk_score": average_risk_score,
            "risk_by_category": risk_by_category
        }
