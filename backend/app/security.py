from __future__ import annotations

from functools import wraps

from flask import abort, g, request

from app.extensions.db import db
from app.models import RefreshTokenSession, TenantMembership, TenantRole, User
from app.services.auth_service import AuthError, decode_token


def _load_context():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        abort(401, description="Missing bearer token")

    token = auth_header.split(" ", 1)[1]
    try:
        payload = decode_token(token, "access")
    except AuthError as exc:
        abort(401, description=str(exc))

    user = db.session.get(User, payload["sub"])
    membership = db.session.get(TenantMembership, payload["membership_id"])
    session = db.session.get(RefreshTokenSession, payload["session_id"])
    if (
        user is None
        or membership is None
        or membership.user_id != user.id
        or session is None
        or session.revoked_at is not None
    ):
        abort(401, description="Session no longer valid")

    g.current_user = user
    g.current_membership = membership
    g.current_tenant = membership.tenant
    g.current_session = session
    g.current_role = membership.role.value


def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        _load_context()
        return fn(*args, **kwargs)

    return wrapper


def role_required(*allowed_roles: TenantRole):
    allowed = {role.value for role in allowed_roles}

    def decorator(fn):
        @wraps(fn)
        @auth_required
        def wrapper(*args, **kwargs):
            if g.current_role not in allowed and not g.current_user.is_system_admin:
                abort(403, description="Insufficient permissions")
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def system_admin_required(fn):
    @wraps(fn)
    @auth_required
    def wrapper(*args, **kwargs):
        if not g.current_user.is_system_admin:
            abort(403, description="System administrator access required")
        return fn(*args, **kwargs)

    return wrapper
