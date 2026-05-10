from __future__ import annotations

from flask import Response, current_app, g, stream_with_context
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from app.models import TenantRole
from app.schemas.chat import (
    ChatMessageCreateSchema,
    ChatSessionCreateSchema,
    ChatSessionDetailSchema,
    ChatSessionListSchema,
    ChatSessionSchema,
)
from app.security import role_required
from app.services.chat_service import ChatNotFoundError, ChatService
from app.services.ollama_chat_service import OllamaChatService

blp = Blueprint("chat", __name__, url_prefix="/api/chat", description="Ollama chat APIs")


def _build_service() -> ChatService:
    ollama_service = OllamaChatService(
        current_app.config["OLLAMA_BASE_URL"],
        timeout=current_app.config["OLLAMA_TIMEOUT"],
    )
    return ChatService(ollama_service, current_app.config["OLLAMA_MODEL"])


@blp.route("/sessions")
class ChatSessionListResource(MethodView):
    @role_required(TenantRole.OWNER, TenantRole.ADMIN, TenantRole.VIEWER)
    @blp.response(200, ChatSessionListSchema)
    def get(self):
        return _build_service().list_sessions(tenant_id=g.current_tenant.id, user_id=g.current_user.id)

    @role_required(TenantRole.OWNER, TenantRole.ADMIN, TenantRole.VIEWER)
    @blp.arguments(ChatSessionCreateSchema)
    @blp.response(201, ChatSessionSchema)
    def post(self, args):
        return _build_service().create_session(
            tenant_id=g.current_tenant.id,
            user_id=g.current_user.id,
            model=args.get("model") or "",
            title=args.get("title") or "",
        )


@blp.route("/sessions/<session_id>")
class ChatSessionResource(MethodView):
    @role_required(TenantRole.OWNER, TenantRole.ADMIN, TenantRole.VIEWER)
    @blp.response(200, ChatSessionDetailSchema)
    def get(self, session_id: str):
        try:
            return _build_service().get_detail(
                tenant_id=g.current_tenant.id,
                user_id=g.current_user.id,
                session_id=session_id,
            )
        except ChatNotFoundError as exc:
            abort(404, message=str(exc))

    @role_required(TenantRole.OWNER, TenantRole.ADMIN, TenantRole.VIEWER)
    def delete(self, session_id: str):
        try:
            _build_service().delete_session(
                tenant_id=g.current_tenant.id,
                user_id=g.current_user.id,
                session_id=session_id,
            )
        except ChatNotFoundError as exc:
            abort(404, message=str(exc))
        return "", 204


@blp.route("/sessions/<session_id>/stream")
class ChatStreamResource(MethodView):
    @role_required(TenantRole.OWNER, TenantRole.ADMIN, TenantRole.VIEWER)
    @blp.arguments(ChatMessageCreateSchema)
    def post(self, args, session_id: str):
        try:
            stream = _build_service().stream_response(
                tenant_id=g.current_tenant.id,
                user_id=g.current_user.id,
                session_id=session_id,
                message=args["message"],
            )
        except ChatNotFoundError as exc:
            abort(404, message=str(exc))

        return Response(
            stream_with_context(stream),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
