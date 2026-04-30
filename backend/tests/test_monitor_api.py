from unittest.mock import patch

from datetime import UTC, datetime

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
        system_tenant = Tenant(name="System Tenant", slug="system")
        demo_tenant = Tenant(name="Demo Tenant", slug="demo")
        other_tenant = Tenant(name="Other Tenant", slug="other")
        sysadmin = User(
            email="sysadmin@example.local",
            full_name="System Administrator",
            password_hash=hash_password("ChangeMe123!"),
            is_system_admin=True,
        )
        user = User(
            email="viewer@example.local",
            full_name="Viewer User",
            password_hash=hash_password("Password123!"),
        )
        db.session.add_all([system_tenant, demo_tenant, other_tenant, user, sysadmin])
        db.session.flush()
        db.session.add_all(
            [
                TenantMembership(tenant_id=system_tenant.id, user_id=sysadmin.id, role=TenantRole.OWNER),
                TenantMembership(tenant_id=demo_tenant.id, user_id=user.id, role=TenantRole.VIEWER),
                TenantMembership(tenant_id=other_tenant.id, user_id=user.id, role=TenantRole.ADMIN),
            ]
        )
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, tenant_slug: str, email: str, password: str):
    response = client.post(
        "/api/auth/login",
        json={"tenantSlug": tenant_slug, "identifier": email, "password": password},
    )
    return response.get_json()


def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_login_success(client):
    payload = login(client, "demo", "viewer@example.local", "Password123!")

    assert payload["user"]["email"] == "viewer@example.local"
    assert payload["tenant"]["slug"] == "demo"
    assert payload["membershipRole"] == "viewer"


def test_login_same_user_different_tenant_context(client):
    payload = login(client, "other", "viewer@example.local", "Password123!")

    assert payload["tenant"]["slug"] == "other"
    assert payload["membershipRole"] == "admin"


def test_login_invalid_password(client):
    response = client.post(
        "/api/auth/login",
        json={"tenantSlug": "demo", "identifier": "viewer@example.local", "password": "bad"},
    )

    assert response.status_code == 401


def test_monitor_requires_auth(client):
    response = client.get("/api/monitor/overview")

    assert response.status_code == 401


def test_viewer_can_access_monitor(client):
    login_payload = login(client, "demo", "viewer@example.local", "Password123!")
    with patch("app.api.monitor._build_service") as service_factory:
        service_factory.return_value.get_overview.return_value = {
            "generatedAt": datetime(2026, 4, 24, 15, 0, tzinfo=UTC),
            "items": [{"metric": "cpu", "label": "CPU", "value": 42.5, "unit": "%"}],
        }
        response = client.get("/api/monitor/overview", headers=auth_header(login_payload["accessToken"]))

    assert response.status_code == 200
    assert response.get_json()["items"][0]["metric"] == "cpu"


def test_viewer_can_access_gpu_depth_timeseries(client):
    login_payload = login(client, "demo", "viewer@example.local", "Password123!")
    with patch("app.api.monitor._build_service") as service_factory:
        service_factory.return_value.get_timeseries.return_value = {
            "metric": "gpu_utilization",
            "range": "1h",
            "step": "1m",
            "series": [],
        }
        response = client.get(
            "/api/monitor/timeseries?metric=gpu_utilization&range=1h&step=1m",
            headers=auth_header(login_payload["accessToken"]),
        )

    assert response.status_code == 200
    assert response.get_json()["metric"] == "gpu_utilization"


def test_system_admin_can_create_tenant(client):
    login_payload = login(client, "system", "sysadmin@example.local", "ChangeMe123!")
    response = client.post(
        "/api/system/tenants",
        headers=auth_header(login_payload["accessToken"]),
        json={"name": "Acme", "slug": "acme"},
    )

    assert response.status_code == 201
    assert response.get_json()["slug"] == "acme"
