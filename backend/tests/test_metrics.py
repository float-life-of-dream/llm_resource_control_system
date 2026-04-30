from __future__ import annotations

from app import create_app
from app.extensions.db import db
from app.extensions.metrics import record_analysis_run
from app.models import Tenant, TenantMembership, TenantRole, User
from app.services.auth_service import hash_password
from prometheus_client import REGISTRY


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
        tenant = Tenant(name="Demo Tenant", slug="demo")
        user = User(
            email="viewer@example.local",
            full_name="Viewer User",
            password_hash=hash_password("Password123!"),
        )
        db.session.add_all([tenant, user])
        db.session.flush()
        db.session.add(TenantMembership(tenant_id=tenant.id, user_id=user.id, role=TenantRole.VIEWER))
        db.session.commit()
    return app


def test_metrics_endpoint_exposes_prometheus_text():
    app = make_app()
    client = app.test_client()

    response = client.get("/metrics")

    assert response.status_code == 200
    payload = response.get_data(as_text=True)
    assert "http_requests_total" in payload
    assert "analysis_run_total" in payload


def test_analysis_metrics_are_recorded():
    before_total = REGISTRY.get_sample_value("analysis_run_total")
    before_failed = REGISTRY.get_sample_value("analysis_run_failed_total")

    record_analysis_run(success=True)
    record_analysis_run(success=False)

    after_total = REGISTRY.get_sample_value("analysis_run_total")
    after_failed = REGISTRY.get_sample_value("analysis_run_failed_total")

    assert after_total == before_total + 2
    assert after_failed == before_failed + 1
