from __future__ import annotations

from app.extensions.db import db
from app.models import RefreshTokenSession, Tenant, TenantMembership, TenantRole, User
from app.services.auth_service import AuthError, hash_password


def create_tenant(name: str, slug: str):
    if Tenant.query.filter_by(slug=slug).first():
        raise AuthError("Tenant slug already exists")
    tenant = Tenant(name=name, slug=slug)
    db.session.add(tenant)
    db.session.commit()
    return tenant


def create_membership(*, tenant: Tenant, email: str, full_name: str, password: str, role: str):
    user = User.query.filter_by(email=email).first()
    if user is None:
        user = User(email=email, full_name=full_name, password_hash=hash_password(password))
        db.session.add(user)
        db.session.flush()
    else:
        user.full_name = full_name

    existing = TenantMembership.query.filter_by(tenant_id=tenant.id, user_id=user.id).first()
    if existing is not None:
        raise AuthError("User already belongs to this tenant")

    membership = TenantMembership(tenant_id=tenant.id, user_id=user.id, role=TenantRole(role))
    db.session.add(membership)
    db.session.commit()
    return membership


def update_membership_role(membership: TenantMembership, role: str):
    membership.role = TenantRole(role)
    db.session.commit()
    return membership


def delete_membership(membership: TenantMembership):
    RefreshTokenSession.query.filter_by(user_id=membership.user_id, tenant_id=membership.tenant_id).delete()
    db.session.delete(membership)
    db.session.commit()
