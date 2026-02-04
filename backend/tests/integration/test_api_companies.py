"""
Integration tests for /api/companies endpoints.
"""

import pytest


class TestCompaniesAPI:
    """Integration tests for companies endpoints."""

    def test_list_companies_empty(self, client):
        """Should return empty list when no companies exist."""
        response = client.get("/api/companies")

        assert response.status_code == 200
        data = response.json()
        assert data["companies"] == []
        assert data["total"] == 0

    def test_list_companies_with_data(self, client, sample_company):
        """Should return companies list with data."""
        response = client.get("/api/companies")

        assert response.status_code == 200
        data = response.json()
        assert len(data["companies"]) == 1
        assert data["total"] == 1
        assert data["companies"][0]["ticker"] == "AAPL"
        assert data["companies"][0]["name"] == "Apple Inc."

    def test_list_companies_pagination(self, client, db_session):
        """Should respect skip and limit parameters."""
        from app.models import Company

        # Create multiple companies
        for i in range(15):
            company = Company(
                ticker=f"TST{i:02d}",
                name=f"Test Company {i}",
                cik=f"000000000{i:02d}",
                sector="Technology"
            )
            db_session.add(company)
        db_session.commit()

        # Test pagination
        response = client.get("/api/companies?skip=5&limit=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data["companies"]) == 5
        assert data["total"] == 15

    def test_list_companies_filter_by_sector(self, client, db_session):
        """Should filter companies by sector."""
        from app.models import Company

        # Create companies in different sectors
        tech = Company(ticker="TECH", name="Tech Co", cik="0000000001", sector="Technology")
        fin = Company(ticker="FIN", name="Finance Co", cik="0000000002", sector="Finance")
        db_session.add_all([tech, fin])
        db_session.commit()

        response = client.get("/api/companies?sector=Technology")

        assert response.status_code == 200
        data = response.json()
        assert len(data["companies"]) == 1
        assert data["companies"][0]["ticker"] == "TECH"

    def test_get_company_by_ticker(self, client, sample_company):
        """Should return company details by ticker."""
        response = client.get("/api/companies/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert data["name"] == "Apple Inc."
        assert data["cik"] == "0000320193"
        assert "filings" in data
        assert "risk_scores" in data

    def test_get_company_case_insensitive(self, client, sample_company):
        """Should handle ticker in any case."""
        response = client.get("/api/companies/aapl")

        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"

    def test_get_company_not_found(self, client):
        """Should return 404 for unknown ticker."""
        response = client.get("/api/companies/INVALID")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_company_with_analysis(self, client, sample_analysis):
        """Should include analysis data for company with completed filing."""
        response = client.get("/api/companies/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert data["latest_analysis"] is not None
        assert "summary" in data["latest_analysis"]
        assert data["risk_scores"] is not None

    def test_list_sectors(self, client, db_session):
        """Should return list of unique sectors."""
        from app.models import Company

        tech = Company(ticker="T1", name="Tech 1", cik="0000000001", sector="Technology")
        fin = Company(ticker="F1", name="Fin 1", cik="0000000002", sector="Finance")
        tech2 = Company(ticker="T2", name="Tech 2", cik="0000000003", sector="Technology")
        db_session.add_all([tech, fin, tech2])
        db_session.commit()

        response = client.get("/api/companies/sectors/list")

        assert response.status_code == 200
        data = response.json()
        assert "sectors" in data
        assert set(data["sectors"]) == {"Technology", "Finance"}
