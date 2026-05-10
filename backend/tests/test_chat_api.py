from __future__ import annotations

import importlib

import pytest

from app import create_app
from app.extensions.db import db
from app.models import ChatMessage, ChatRole, ChatSession, Tenant, TenantMembership, TenantRole, User
from app.services.auth_service import hash_password


class FakeOllamaChatService:
    def __init__(self):
        self.messages = []

    def stream_chat(self, *, model: str, messages: list[dict]):
        self.messages = messages
        yield {"message": {"content": "hello"}, "done": False}
        yield {"message": {"content": " world"}, "done": True}


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
                TenantMembership(tenant_id=other_tenant.id, user_id=user.id, role=TenantRole.VIEWER),
            ]
        )
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, tenant_slug: str):
    response = client.post(
        "/api/auth/login",
        json={"tenantSlug": tenant_slug, "identifier": "viewer@example.local", "password": "Password123!"},
    )
    return response.get_json()


def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_chat_requires_auth(client):
    response = client.get("/api/chat/sessions")

    assert response.status_code == 401


def test_viewer_can_create_and_list_chat_session(client):
    payload = login(client, "demo")

    create_response = client.post(
        "/api/chat/sessions",
        headers=auth_header(payload["accessToken"]),
        json={"title": "Ops chat"},
    )
    list_response = client.get("/api/chat/sessions", headers=auth_header(payload["accessToken"]))

    assert create_response.status_code == 201
    assert create_response.get_json()["title"] == "Ops chat"
    assert list_response.get_json()["items"][0]["title"] == "Ops chat"


def test_chat_sessions_are_tenant_scoped(client):
    demo = login(client, "demo")
    other = login(client, "other")

    create_response = client.post(
        "/api/chat/sessions",
        headers=auth_header(demo["accessToken"]),
        json={"title": "Demo only"},
    )
    session_id = create_response.get_json()["id"]
    detail = client.get(f"/api/chat/sessions/{session_id}", headers=auth_header(other["accessToken"]))

    assert detail.status_code == 404


def test_stream_chat_persists_user_and_assistant_messages(app, client, monkeypatch):
    payload = login(client, "demo")
    fake_ollama = FakeOllamaChatService()

    def fake_build_service():
        from app.services.chat_service import ChatService

        return ChatService(fake_ollama, "llama3.1:8b")

    chat_api = importlib.import_module("app.api.chat")
    monkeypatch.setattr(chat_api, "_build_service", fake_build_service)
    create_response = client.post("/api/chat/sessions", headers=auth_header(payload["accessToken"]), json={})
    session_id = create_response.get_json()["id"]
    response = client.post(
        f"/api/chat/sessions/{session_id}/stream",
        headers=auth_header(payload["accessToken"]),
        json={"message": "Say hello"},
    )

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "event: message" in body
    assert "hello" in body
    with app.app_context():
        session = db.session.get(ChatSession, session_id)
        messages = ChatMessage.query.filter_by(session_id=session.id).order_by(ChatMessage.created_at.asc()).all()
        assert [message.role for message in messages] == [ChatRole.USER, ChatRole.ASSISTANT]
        assert messages[1].content == "hello world"
        assert fake_ollama.messages[0]["content"] == "Say hello"
