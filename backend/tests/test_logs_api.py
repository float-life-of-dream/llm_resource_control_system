from __future__ import annotations

from unittest.mock import patch

import pytest

from app import create_app
from app.extensions.db import db
from app.models import Tenant, TenantMembership, TenantRole, User
from app.services.auth_service import hash_password
from app.services.elasticsearch_log_service import ElasticsearchLogError, ElasticsearchLogService


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
        demo_tenant = Tenant(name="Demo Tenant", slug="demo")
        user = User(
            email="viewer@example.local",
            full_name="Viewer User",
            password_hash=hash_password("Password123!"),
        )
        db.session.add_all([demo_tenant, user])
        db.session.flush()
        db.session.add(TenantMembership(tenant_id=demo_tenant.id, user_id=user.id, role=TenantRole.VIEWER))
        db.session.commit()
        tenant_id = demo_tenant.id
        yield app, tenant_id
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app[0].test_client()


def login(client):
    response = client.post(
        "/api/auth/login",
        json={"tenantSlug": "demo", "identifier": "viewer@example.local", "password": "Password123!"},
    )
    return response.get_json()


def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_logs_require_auth(client):
    response = client.get("/api/logs/search")

    assert response.status_code == 401


def test_viewer_can_search_logs(client):
    payload = login(client)
    with patch("app.api.logs._build_service") as service_factory:
        service_factory.return_value.search_log_page.return_value = {
            "total": 1,
            "items": [
                {
                    "timestamp": "2026-04-30T10:00:00Z",
                    "level": "error",
                    "service": "backend",
                    "message": "timeout",
                    "traceId": "trace-1",
                    "host": "node-1",
                    "source": "logs-2026",
                }
            ],
        }
        response = client.get(
            "/api/logs/search?range=1h&query=timeout&level=error&service=backend&limit=100",
            headers=auth_header(payload["accessToken"]),
        )

    assert response.status_code == 200
    body = response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["traceId"] == "trace-1"
    service_factory.return_value.search_log_page.assert_called_once()
    _, kwargs = service_factory.return_value.search_log_page.call_args
    assert kwargs["log_query"] == "timeout"
    assert kwargs["level"] == "error"
    assert kwargs["service"] == "backend"


def test_logs_summary_and_services(client):
    payload = login(client)
    with patch("app.api.logs._build_service") as service_factory:
        service_factory.return_value.get_summary.return_value = {
            "total": 2,
            "levels": [{"key": "error", "count": 2}],
            "services": [{"key": "backend", "count": 2}],
        }
        summary = client.get("/api/logs/summary?range=1h&query=timeout", headers=auth_header(payload["accessToken"]))
        service_factory.return_value.get_services.return_value = ["backend"]
        services = client.get("/api/logs/services?range=24h", headers=auth_header(payload["accessToken"]))

    assert summary.status_code == 200
    assert summary.get_json()["levels"][0]["key"] == "error"
    assert services.status_code == 200
    assert services.get_json()["items"] == ["backend"]


def test_logs_elasticsearch_error_returns_502(client):
    payload = login(client)
    with patch("app.api.logs._build_service") as service_factory:
        service_factory.return_value.search_log_page.side_effect = ElasticsearchLogError("Elasticsearch request failed")
        response = client.get("/api/logs/search", headers=auth_header(payload["accessToken"]))

    assert response.status_code == 502


def test_elasticsearch_search_dsl_includes_tenant_filters(app):
    _, tenant_id = app
    service = ElasticsearchLogService("http://elasticsearch:9200", "logs-*")
    payload = service._build_search_payload(
        tenant_id=tenant_id,
        range_value="1h",
        log_query="timeout",
        level="error",
        service="backend",
        size=100,
    )

    filters = payload["query"]["bool"]["filter"]
    assert {"term": {"tenant_id.keyword": tenant_id}} in filters[1]["bool"]["should"]
    assert payload["query"]["bool"]["must"][0]["simple_query_string"]["query"] == "timeout"
    assert filters[2]["bool"]["should"][0] == {"term": {"log.level.keyword": "error"}}
    assert filters[3]["bool"]["should"][0] == {"term": {"service.name.keyword": "backend"}}
