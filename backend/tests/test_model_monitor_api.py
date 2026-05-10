from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from app import create_app
from app.extensions.db import db
from app.models import Tenant, TenantMembership, TenantRole, User
from app.services.auth_service import hash_password


@pytest.fixture
def app():
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
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def login(client):
    response = client.post(
        "/api/auth/login",
        json={"tenantSlug": "demo", "identifier": "viewer@example.local", "password": "Password123!"},
    )
    return response.get_json()


def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_model_monitor_requires_auth(client):
    response = client.get("/api/model-monitor/overview")

    assert response.status_code == 401


def test_viewer_can_access_model_monitor_overview(client):
    login_payload = login(client)
    with patch("app.api.model_monitor._build_service") as service_factory:
        service_factory.return_value.get_overview.return_value = {
            "generatedAt": datetime(2026, 4, 29, 9, 0, tzinfo=UTC),
            "items": [{"metric": "request_rate", "label": "Request Rate", "value": 1.5, "unit": "req/s"}],
        }
        response = client.get("/api/model-monitor/overview", headers=auth_header(login_payload["accessToken"]))

    assert response.status_code == 200
    assert response.get_json()["items"][0]["metric"] == "request_rate"


def test_viewer_can_access_model_list(client):
    login_payload = login(client)
    with patch("app.api.model_monitor._build_service") as service_factory:
        service_factory.return_value.get_models.return_value = {
            "generatedAt": datetime(2026, 4, 29, 9, 0, tzinfo=UTC),
            "items": [
                {
                    "name": "llama3.1:8b",
                    "parameterSize": "8.0B",
                    "quantization": "Q4_K_M",
                    "contextWindow": 8192,
                    "memoryBytes": 4_294_967_296,
                    "status": "loaded",
                    "lastSeenAt": datetime(2026, 4, 29, 9, 0, tzinfo=UTC),
                }
            ],
        }
        response = client.get("/api/model-monitor/models", headers=auth_header(login_payload["accessToken"]))

    assert response.status_code == 200
    assert response.get_json()["items"][0]["name"] == "llama3.1:8b"


def test_viewer_can_access_extended_model_timeseries(client):
    login_payload = login(client)
    with patch("app.api.model_monitor._build_service") as service_factory:
        service_factory.return_value.get_timeseries.return_value = {
            "metric": "tokens_per_second",
            "range": "1h",
            "step": "1m",
            "series": [],
        }
        response = client.get(
            "/api/model-monitor/timeseries?metric=tokens_per_second&range=1h&step=1m",
            headers=auth_header(login_payload["accessToken"]),
        )

    assert response.status_code == 200
    assert response.get_json()["metric"] == "tokens_per_second"
