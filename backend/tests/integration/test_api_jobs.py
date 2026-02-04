"""
Integration tests for /api/jobs endpoints.
"""

import pytest
from app.models import Job


class TestJobsAPI:
    """Integration tests for jobs endpoints."""

    def test_fetch_all_starts_job(self, client, db_session):
        """Should create and start a fetch job."""
        response = client.post("/api/jobs/fetch-all")

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "started"

        # Verify job was created in database
        job = db_session.query(Job).filter(Job.id == data["job_id"]).first()
        assert job is not None
        assert job.job_type == "fetch"

    def test_fetch_all_blocks_concurrent(self, client, db_session):
        """Should prevent concurrent fetch jobs."""
        # Create a running job
        running_job = Job(job_type="fetch", status="running")
        db_session.add(running_job)
        db_session.commit()

        response = client.post("/api/jobs/fetch-all")

        assert response.status_code == 400
        assert "already running" in response.json()["detail"].lower()

    def test_analyze_all_starts_job(self, client, db_session):
        """Should create and start an analyze job."""
        response = client.post("/api/jobs/analyze-all")

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "started"

        # Verify job was created
        job = db_session.query(Job).filter(Job.id == data["job_id"]).first()
        assert job is not None
        assert job.job_type == "analyze"

    def test_analyze_all_blocks_concurrent(self, client, db_session):
        """Should prevent concurrent analyze jobs."""
        # Create a running job
        running_job = Job(job_type="analyze", status="running")
        db_session.add(running_job)
        db_session.commit()

        response = client.post("/api/jobs/analyze-all")

        assert response.status_code == 400
        assert "already running" in response.json()["detail"].lower()

    def test_get_job_status_by_id(self, client, db_session):
        """Should return job status by ID."""
        job = Job(job_type="fetch", status="completed", total_items=100, completed_items=100)
        db_session.add(job)
        db_session.commit()

        response = client.get(f"/api/jobs/status?job_id={job.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job.id
        assert data["status"] == "completed"
        assert data["total_items"] == 100

    def test_get_job_status_latest(self, client, db_session):
        """Should return most recent job when no ID specified."""
        job1 = Job(job_type="fetch", status="completed")
        job2 = Job(job_type="analyze", status="running")
        db_session.add_all([job1, job2])
        db_session.commit()

        response = client.get("/api/jobs/status")

        assert response.status_code == 200
        data = response.json()
        # Should be the most recently created job
        assert data["job_type"] == "analyze"

    def test_get_job_status_empty(self, client):
        """Should return null when no jobs exist."""
        response = client.get("/api/jobs/status")

        assert response.status_code == 200
        assert response.json() is None

    def test_get_job_history(self, client, db_session):
        """Should return job history."""
        # Create multiple jobs
        for i in range(5):
            job = Job(job_type="fetch" if i % 2 == 0 else "analyze", status="completed")
            db_session.add(job)
        db_session.commit()

        response = client.get("/api/jobs/history")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_get_job_history_limit(self, client, db_session):
        """Should respect limit parameter."""
        for i in range(10):
            job = Job(job_type="fetch", status="completed")
            db_session.add(job)
        db_session.commit()

        response = client.get("/api/jobs/history?limit=3")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_risk_summary_empty(self, client):
        """Should return zeros for empty database."""
        response = client.get("/api/jobs/risk-summary")

        assert response.status_code == 200
        data = response.json()
        assert data["total_companies"] == 0
        assert data["analyzed_companies"] == 0

    def test_get_risk_summary_with_data(self, client, sample_analysis):
        """Should return correct summary with analyzed companies."""
        response = client.get("/api/jobs/risk-summary")

        assert response.status_code == 200
        data = response.json()
        assert data["total_companies"] == 1
        assert data["analyzed_companies"] == 1
        assert "risk_by_category" in data
