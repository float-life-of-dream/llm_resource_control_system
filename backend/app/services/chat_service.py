from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Iterator

from app.extensions.db import db
from app.models import ChatMessage, ChatRole, ChatSession
from app.services.ollama_chat_service import OllamaChatError, OllamaChatService


class ChatNotFoundError(LookupError):
    pass


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=True)}\n\n"


@dataclass
class ChatService:
    ollama_service: OllamaChatService
    default_model: str

    def create_session(self, *, tenant_id: str, user_id: str, model: str, title: str) -> ChatSession:
        selected_model = model.strip() or self.default_model
        session = ChatSession(
            tenant_id=tenant_id,
            user_id=user_id,
            model=selected_model,
            title=title.strip() or "New chat",
        )
        db.session.add(session)
        db.session.commit()
        return session

    def list_sessions(self, *, tenant_id: str, user_id: str) -> dict:
        items = (
            ChatSession.query.filter_by(tenant_id=tenant_id, user_id=user_id, is_deleted=False)
            .order_by(ChatSession.updated_at.desc())
            .all()
        )
        return {"items": items}

    def get_detail(self, *, tenant_id: str, user_id: str, session_id: str) -> dict:
        session = self._get_session(tenant_id, user_id, session_id)
        return {"session": session, "messages": session.messages}

    def delete_session(self, *, tenant_id: str, user_id: str, session_id: str) -> None:
        session = self._get_session(tenant_id, user_id, session_id)
        session.is_deleted = True
        session.updated_at = datetime.now(UTC)
        db.session.commit()

    def stream_response(self, *, tenant_id: str, user_id: str, session_id: str, message: str) -> Iterator[str]:
        session = self._get_session(tenant_id, user_id, session_id)
        user_message = ChatMessage(session_id=session.id, role=ChatRole.USER, content=message.strip(), raw_metadata={})
        db.session.add(user_message)
        if session.title == "New chat":
            session.title = message.strip()[:80] or session.title
        session.updated_at = datetime.now(UTC)
        db.session.commit()

        history = [
            {"role": item.role.value, "content": item.content}
            for item in ChatMessage.query.filter_by(session_id=session.id).order_by(ChatMessage.created_at.asc()).all()
        ]
        chunks: list[str] = []
        raw_events: list[dict] = []

        def generate() -> Iterator[str]:
            try:
                for payload in self.ollama_service.stream_chat(model=session.model, messages=history):
                    raw_events.append(payload)
                    content = str((payload.get("message") or {}).get("content") or "")
                    if content:
                        chunks.append(content)
                        yield _sse("message", {"content": content})
                    if payload.get("done"):
                        break

                assistant_content = "".join(chunks)
                assistant_message = ChatMessage(
                    session_id=session.id,
                    role=ChatRole.ASSISTANT,
                    content=assistant_content,
                    raw_metadata={"events": raw_events[-5:]},
                )
                db.session.add(assistant_message)
                session.updated_at = datetime.now(UTC)
                db.session.commit()
                yield _sse("done", {"messageId": assistant_message.id})
            except OllamaChatError as exc:
                db.session.add(
                    ChatMessage(
                        session_id=session.id,
                        role=ChatRole.ASSISTANT,
                        content="",
                        raw_metadata={"error": str(exc), "events": raw_events[-5:]},
                    )
                )
                session.updated_at = datetime.now(UTC)
                db.session.commit()
                yield _sse("error", {"message": str(exc)})

        return generate()

    @staticmethod
    def _get_session(tenant_id: str, user_id: str, session_id: str) -> ChatSession:
        session = ChatSession.query.filter_by(
            id=session_id,
            tenant_id=tenant_id,
            user_id=user_id,
            is_deleted=False,
        ).first()
        if session is None:
            raise ChatNotFoundError("Chat session not found")
        return session
