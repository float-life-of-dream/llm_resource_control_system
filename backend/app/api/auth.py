from __future__ import annotations

from flask import g, request
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from app.models import RefreshTokenSession
from app.schemas.auth import (
    LoginResponseSchema,
    LoginSchema,
    MeResponseSchema,
    RefreshSchema,
    SessionListSchema,
)
from app.security import auth_required
from app.services.auth_service import AuthError, authenticate, refresh_session, revoke_session

blp = Blueprint("auth", __name__, url_prefix="/api/auth", description="Authentication APIs")


@blp.route("/login")
class LoginResource(MethodView):
    @blp.arguments(LoginSchema)
    @blp.response(200, LoginResponseSchema)
    def post(self, args):
        try:
            return authenticate(args["identifier"], args["password"], args["tenantSlug"])
        except AuthError as exc:
            abort(401, message=str(exc))


@blp.route("/refresh")
class RefreshResource(MethodView):
    @blp.arguments(RefreshSchema)
    @blp.response(200, LoginResponseSchema)
    def post(self, args):
        try:
            return refresh_session(args["refreshToken"])
        except AuthError as exc:
            abort(401, message=str(exc))


@blp.route("/logout")
class LogoutResource(MethodView):
    @auth_required
    def post(self):
        revoke_session(g.current_session.id)
        return {"status": "ok"}


@blp.route("/me")
class MeResource(MethodView):
    @auth_required
    @blp.response(200, MeResponseSchema)
    def get(self):
        return {
            "user": g.current_user,
            "tenant": g.current_tenant,
            "membershipRole": g.current_role,
        }


@blp.route("/sessions")
class SessionListResource(MethodView):
    @auth_required
    @blp.response(200, SessionListSchema)
    def get(self):
        sessions = RefreshTokenSession.query.filter_by(
            user_id=g.current_user.id,
            tenant_id=g.current_tenant.id,
        ).order_by(RefreshTokenSession.created_at.desc()).all()
        return {"items": sessions}


@blp.route("/sessions/<session_id>")
class SessionDeleteResource(MethodView):
    @auth_required
    def delete(self, session_id: str):
        session = RefreshTokenSession.query.filter_by(
            id=session_id,
            user_id=g.current_user.id,
            tenant_id=g.current_tenant.id,
        ).first()
        if session is None:
            abort(404, message="Session not found")
        revoke_session(session.id)
        return {"status": "ok"}
