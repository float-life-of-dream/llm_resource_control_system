from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

from app import create_app
from app.extensions.db import db
from app.models import AnalysisEvidence, AnalysisResult, AnalysisSession, AnalysisStatus, Tenant, TenantMembership, TenantRole, User
from app.services.auth_service import hash_password


def make_app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "JWT_SECRET_KEY": "test-secret",
            "BOOTSTRAP_ADMIN_EMAIL": "sysadmin@example.local",
            "BOOTSTRAP_ADMIN_PASSWORD": "ChangeMe123!",
            "BOOTSTRAP_DEFAULT_TENANT_NAME": "System Tenant",
            "BOOTSTRAP_DEFAULT_TENANT_SLUG": "system",
        }
    )
    with app.app_context():
        db.drop_all()
        db.create_all()
        demo_tenant = Tenant(name="Demo Tenant", slug="demo")
        other_tenant = Tenant(name="Other Tenant", slug="other")
        user = User(
            email="viewer@example.local",
            full_name="Viewer User",
            password_hash=hash_password("Password123!"),
        )
        db.session.add_all([demo_tenant, other_tenant, user])
        db.session.flush()
        db.session.add_all(
            [
                TenantMembership(tenant_id=demo_tenant.id, user_id=user.id, role=TenantRole.VIEWER),
                TenantMembership(tenant_id=other_tenant.id, user_id=user.id, role=TenantRole.ADMIN),
            ]
        )
        db.session.commit()
    return app


def login(client, tenant_slug: str):
    response = client.post(
        "/api/auth/login",
        json={"tenantSlug": tenant_slug, "identifier": "viewer@example.local", "password": "Password123!"},
    )
    return response.get_json()


def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_analysis_requires_auth():
    app = make_app()
    client = app.test_client()
    response = client.post("/api/analysis/run", json={"range": "1h", "logQuery": "", "logLimit": 10, "includeMetrics": True})
    assert response.status_code == 401


def test_viewer_can_run_analysis():
    app = make_app()
    client = app.test_client()
    payload = login(client, "demo")
    with patch("app.api.analysis._build_service") as service_factory:
        service_factory.return_value.run_analysis.return_value = {
            "analysisId": "analysis-1",
            "status": "completed",
            "summary": "All good",
            "anomalies": [],
            "recommendations": ["Keep watching"],
            "evidenceSummary": {"metrics": ["cpu"], "logCount": 1},
            "model": "llama3.1:8b",
            "durationMs": 1200,
        }
        response = client.post(
            "/api/analysis/run",
            headers=auth_header(payload["accessToken"]),
            json={"range": "1h", "logQuery": "timeout", "logLimit": 10, "includeMetrics": True},
        )

    assert response.status_code == 200
    assert response.get_json()["analysisId"] == "analysis-1"


def test_analysis_history_is_tenant_scoped():
    app = make_app()
    client = app.test_client()
    demo = login(client, "demo")
    other = login(client, "other")

    with app.app_context():
        demo_tenant = Tenant.query.filter_by(slug="demo").first()
        other_tenant = Tenant.query.filter_by(slug="other").first()
        user = User.query.filter_by(email="viewer@example.local").first()
        session = AnalysisSession(
            tenant_id=other_tenant.id,
            user_id=user.id,
            range_value="1h",
            log_query="timeout",
            log_limit=10,
            include_metrics=True,
            status=AnalysisStatus.COMPLETED,
            model_name="llama3.1:8b",
            duration_ms=1200,
            created_at=datetime(2026, 4, 27, 9, 0, tzinfo=UTC),
            completed_at=datetime(2026, 4, 27, 9, 1, tzinfo=UTC),
        )
        db.session.add(session)
        db.session.flush()
        db.session.add(
            AnalysisResult(
                analysis_session_id=session.id,
                summary="Other tenant result",
                anomalies=["issue"],
                recommendations=["fix"],
                raw_model_output="{}",
            )
        )
        db.session.add(
            AnalysisEvidence(
                analysis_session_id=session.id,
                metrics_snapshot={"cpu": {"current": 42.5}},
                log_excerpt=[{"message": "timeout"}],
            )
        )
        db.session.commit()

    response = client.get("/api/analysis/history", headers=auth_header(demo["accessToken"]))
    assert response.status_code == 200
    assert response.get_json()["items"] == []

    detail = client.get(f"/api/analysis/history/{session.id}", headers=auth_header(demo["accessToken"]))
    assert detail.status_code == 404

    other_response = client.get("/api/analysis/history", headers=auth_header(other["accessToken"]))
    assert other_response.status_code == 200
    assert other_response.get_json()["items"][0]["summary"] == "Other tenant result"
