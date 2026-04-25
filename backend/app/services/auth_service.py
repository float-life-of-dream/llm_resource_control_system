from __future__ import annotations

import uuid
from datetime import UTC, datetime

import jwt
from flask import current_app, request
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions.db import db
from app.models import RefreshTokenSession, Tenant, TenantMembership, TenantRole, User


class AuthError(RuntimeError):
    pass


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    return check_password_hash(password_hash, password)


def _token_payload(user: User, membership: TenantMembership, session: RefreshTokenSession, token_type: str, expires_at: datetime):
    return {
        "sub": user.id,
        "tenant_id": membership.tenant_id,
        "membership_id": membership.id,
        "role": membership.role.value,
        "system_admin": user.is_system_admin,
        "session_id": session.id,
        "type": token_type,
        "jti": session.refresh_jti if token_type == "refresh" else str(uuid.uuid4()),
        "exp": expires_at,
        "iat": datetime.now(UTC),
    }


def issue_tokens(user: User, membership: TenantMembership):
    now = datetime.now(UTC)
    refresh_expires = now + current_app.config["JWT_REFRESH_TTL"]
    access_expires = now + current_app.config["JWT_ACCESS_TTL"]
    session = RefreshTokenSession(
        user_id=user.id,
        tenant_id=membership.tenant_id,
        refresh_jti=str(uuid.uuid4()),
        user_agent=request.headers.get("User-Agent"),
        ip_address=request.remote_addr,
        expires_at=refresh_expires,
        last_used_at=now,
    )
    db.session.add(session)
    db.session.flush()

    access_token = jwt.encode(
        _token_payload(user, membership, session, "access", access_expires),
        current_app.config["JWT_SECRET_KEY"],
        algorithm="HS256",
    )
    refresh_token = jwt.encode(
        _token_payload(user, membership, session, "refresh", refresh_expires),
        current_app.config["JWT_SECRET_KEY"],
        algorithm="HS256",
    )
    db.session.commit()
    return {
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "expiresIn": int(current_app.config["JWT_ACCESS_TTL"].total_seconds()),
        "user": user,
        "tenant": membership.tenant,
        "membershipRole": membership.role.value,
    }


def decode_token(token: str, expected_type: str):
    try:
        payload = jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
    except jwt.InvalidTokenError as exc:
        raise AuthError("Invalid token") from exc

    if payload.get("type") != expected_type:
        raise AuthError("Invalid token type")
    return payload


def authenticate(identifier: str, password: str, tenant_slug: str):
    tenant = Tenant.query.filter_by(slug=tenant_slug).first()
    if tenant is None:
        raise AuthError("Tenant not found")

    user = User.query.filter_by(email=identifier).first()
    if user is None or not user.is_active or not verify_password(user.password_hash, password):
        raise AuthError("Invalid credentials")

    membership = TenantMembership.query.filter_by(tenant_id=tenant.id, user_id=user.id).first()
    if membership is None:
        raise AuthError("Membership not found")

    return issue_tokens(user, membership)


def refresh_session(refresh_token: str):
    payload = decode_token(refresh_token, "refresh")
    session = RefreshTokenSession.query.filter_by(id=payload["session_id"]).first()
    if session is None or session.revoked_at is not None or session.expires_at <= datetime.now(UTC):
        raise AuthError("Refresh session is no longer valid")
    if session.refresh_jti != payload["jti"]:
        raise AuthError("Refresh session has been rotated")

    user = db.session.get(User, payload["sub"])
    membership = db.session.get(TenantMembership, payload["membership_id"])
    if user is None or membership is None or membership.user_id != user.id:
        raise AuthError("Refresh session no longer maps to a valid membership")

    session.refresh_jti = str(uuid.uuid4())
    session.last_used_at = datetime.now(UTC)
    db.session.flush()

    access_expires = datetime.now(UTC) + current_app.config["JWT_ACCESS_TTL"]
    refresh_expires = datetime.now(UTC) + current_app.config["JWT_REFRESH_TTL"]
    session.expires_at = refresh_expires

    access_token = jwt.encode(
        _token_payload(user, membership, session, "access", access_expires),
        current_app.config["JWT_SECRET_KEY"],
        algorithm="HS256",
    )
    rotated_refresh = jwt.encode(
        _token_payload(user, membership, session, "refresh", refresh_expires),
        current_app.config["JWT_SECRET_KEY"],
        algorithm="HS256",
    )
    db.session.commit()
    return {
        "accessToken": access_token,
        "refreshToken": rotated_refresh,
        "expiresIn": int(current_app.config["JWT_ACCESS_TTL"].total_seconds()),
        "user": user,
        "tenant": membership.tenant,
        "membershipRole": membership.role.value,
    }


def revoke_session(session_id: str):
    session = db.session.get(RefreshTokenSession, session_id)
    if session is None:
        raise AuthError("Session not found")
    if session.revoked_at is None:
        session.revoked_at = datetime.now(UTC)
        db.session.commit()
    return session


def bootstrap_security():
    db.create_all()

    tenant_slug = current_app.config["BOOTSTRAP_DEFAULT_TENANT_SLUG"]
    tenant = Tenant.query.filter_by(slug=tenant_slug).first()
    if tenant is None:
        tenant = Tenant(
            name=current_app.config["BOOTSTRAP_DEFAULT_TENANT_NAME"],
            slug=tenant_slug,
        )
        db.session.add(tenant)
        db.session.flush()

    admin_email = current_app.config["BOOTSTRAP_ADMIN_EMAIL"]
    user = User.query.filter_by(email=admin_email).first()
    if user is None:
        user = User(
            email=admin_email,
            full_name="System Administrator",
            password_hash=hash_password(current_app.config["BOOTSTRAP_ADMIN_PASSWORD"]),
            is_system_admin=True,
        )
        db.session.add(user)
        db.session.flush()

    membership = TenantMembership.query.filter_by(tenant_id=tenant.id, user_id=user.id).first()
    if membership is None:
        db.session.add(TenantMembership(tenant_id=tenant.id, user_id=user.id, role=TenantRole.OWNER))

    db.session.commit()
