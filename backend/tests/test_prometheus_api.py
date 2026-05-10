from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from app import create_app
from app.extensions.db import db
from app.models import Tenant, TenantMembership, TenantRole, User
from app.services.auth_service import hash_password
from app.services.prometheus_client import PrometheusClientError


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


def test_prometheus_status_requires_auth(client):
    response = client.get("/api/prometheus/health")

    assert response.status_code == 401


def test_viewer_can_access_prometheus_health(client):
    token = login(client)["accessToken"]
    with patch("app.api.prometheus._build_service") as service_factory:
        service_factory.return_value.get_health.return_value = {
            "status": "up",
            "baseUrl": "http://prometheus:9090",
            "generatedAt": datetime(2026, 4, 30, 10, 0, tzinfo=UTC),
        }
        response = client.get("/api/prometheus/health", headers=auth_header(token))

    assert response.status_code == 200
    assert response.get_json()["status"] == "up"


def test_prometheus_health_returns_502_when_unavailable(client):
    token = login(client)["accessToken"]
    with patch("app.api.prometheus._build_service") as service_factory:
        service_factory.return_value.get_health.side_effect = PrometheusClientError("Prometheus request failed")
        response = client.get("/api/prometheus/health", headers=auth_header(token))

    assert response.status_code == 502


def test_viewer_can_access_prometheus_targets(client):
    token = login(client)["accessToken"]
    with patch("app.api.prometheus._build_service") as service_factory:
        service_factory.return_value.get_targets.return_value = {
            "generatedAt": datetime(2026, 4, 30, 10, 0, tzinfo=UTC),
            "items": [
                {
                    "job": "backend",
                    "instance": "backend:5000",
                    "health": "up",
                    "scrapeUrl": "http://backend:5000/metrics",
                    "lastScrape": datetime(2026, 4, 30, 10, 0, tzinfo=UTC),
                    "lastError": "",
                }
            ],
        }
        response = client.get("/api/prometheus/targets", headers=auth_header(token))

    assert response.status_code == 200
    assert response.get_json()["items"][0]["job"] == "backend"


def test_metrics_catalog_does_not_expose_raw_query(client):
    token = login(client)["accessToken"]
    response = client.get("/api/prometheus/metrics", headers=auth_header(token))

    assert response.status_code == 200
    payload = response.get_json()
    assert [group["key"] for group in payload["groups"]] == ["host", "gpu", "model"]
    assert "/api/prometheus/query" not in str(payload)
