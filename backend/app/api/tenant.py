from __future__ import annotations

from flask import g
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from app.extensions.db import db
from app.models import TenantMembership, TenantRole
from app.schemas.auth import (
    MemberCreateSchema,
    MembershipListSchema,
    MembershipSchema,
    MemberUpdateSchema,
    TenantSchema,
    TenantUpdateSchema,
)
from app.security import auth_required, role_required
from app.services.auth_service import AuthError
from app.services.tenant_service import create_membership, delete_membership, update_membership_role

blp = Blueprint("tenant", __name__, url_prefix="/api/tenant", description="Tenant management APIs")


@blp.route("")
class TenantResource(MethodView):
    @auth_required
    @blp.response(200, TenantSchema)
    def get(self):
        return g.current_tenant

    @role_required(TenantRole.OWNER, TenantRole.ADMIN)
    @blp.arguments(TenantUpdateSchema)
    @blp.response(200, TenantSchema)
    def patch(self, args):
        g.current_tenant.name = args["name"]
        db.session.commit()
        return g.current_tenant


@blp.route("/members")
class TenantMembersResource(MethodView):
    @role_required(TenantRole.OWNER, TenantRole.ADMIN, TenantRole.VIEWER)
    @blp.response(200, MembershipListSchema)
    def get(self):
        items = TenantMembership.query.filter_by(tenant_id=g.current_tenant.id).all()
        return {"items": items}

    @role_required(TenantRole.OWNER, TenantRole.ADMIN)
    @blp.arguments(MemberCreateSchema)
    @blp.response(201, MembershipSchema)
    def post(self, args):
        if g.current_role == TenantRole.ADMIN.value and args["role"] == TenantRole.OWNER.value:
            abort(403, message="Admins cannot create owners")
        try:
            return create_membership(
                tenant=g.current_tenant,
                email=args["email"],
                full_name=args["fullName"],
                password=args["password"],
                role=args["role"],
            )
        except AuthError as exc:
            abort(400, message=str(exc))


@blp.route("/members/<membership_id>")
class TenantMemberResource(MethodView):
    @role_required(TenantRole.OWNER, TenantRole.ADMIN)
    @blp.arguments(MemberUpdateSchema)
    @blp.response(200, MembershipSchema)
    def patch(self, args, membership_id: str):
        membership = TenantMembership.query.filter_by(id=membership_id, tenant_id=g.current_tenant.id).first()
        if membership is None:
            abort(404, message="Membership not found")
        if g.current_role == TenantRole.ADMIN.value and membership.role == TenantRole.OWNER:
            abort(403, message="Admins cannot modify owners")
        if g.current_role == TenantRole.ADMIN.value and args["role"] == TenantRole.OWNER.value:
            abort(403, message="Admins cannot promote owners")
        return update_membership_role(membership, args["role"])

    @role_required(TenantRole.OWNER, TenantRole.ADMIN)
    def delete(self, membership_id: str):
        membership = TenantMembership.query.filter_by(id=membership_id, tenant_id=g.current_tenant.id).first()
        if membership is None:
            abort(404, message="Membership not found")
        if membership.id == g.current_membership.id:
            abort(400, message="Cannot delete current membership")
        if g.current_role == TenantRole.ADMIN.value and membership.role == TenantRole.OWNER:
            abort(403, message="Admins cannot delete owners")
        delete_membership(membership)
        return {"status": "ok"}
