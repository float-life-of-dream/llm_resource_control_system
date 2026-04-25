from __future__ import annotations

from flask.views import MethodView
from flask_smorest import Blueprint, abort

from app.extensions.db import db
from app.models import Tenant
from app.schemas.auth import MemberCreateSchema, MembershipSchema, SystemTenantsSchema, TenantCreateSchema, TenantSchema
from app.security import system_admin_required
from app.services.auth_service import AuthError
from app.services.tenant_service import create_membership, create_tenant

blp = Blueprint("system", __name__, url_prefix="/api/system", description="System administration APIs")


@blp.route("/tenants")
class SystemTenantsResource(MethodView):
    @system_admin_required
    @blp.response(200, SystemTenantsSchema)
    def get(self):
        return {"items": Tenant.query.order_by(Tenant.created_at.desc()).all()}

    @system_admin_required
    @blp.arguments(TenantCreateSchema)
    @blp.response(201, TenantSchema)
    def post(self, args):
        try:
            return create_tenant(args["name"], args["slug"])
        except AuthError as exc:
            abort(400, message=str(exc))


@blp.route("/tenants/<tenant_id>/members")
class SystemTenantMembersResource(MethodView):
    @system_admin_required
    @blp.arguments(MemberCreateSchema)
    @blp.response(201, MembershipSchema)
    def post(self, args, tenant_id: str):
        tenant = db.session.get(Tenant, tenant_id)
        if tenant is None:
            abort(404, message="Tenant not found")
        try:
            return create_membership(
                tenant=tenant,
                email=args["email"],
                full_name=args["fullName"],
                password=args["password"],
                role=args["role"],
            )
        except AuthError as exc:
            abort(400, message=str(exc))
