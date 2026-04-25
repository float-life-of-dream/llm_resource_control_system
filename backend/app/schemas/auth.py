from __future__ import annotations

from marshmallow import Schema, fields, validate


class UserSchema(Schema):
    id = fields.String(required=True)
    email = fields.Email(required=True)
    fullName = fields.String(attribute="full_name", required=True)
    isSystemAdmin = fields.Boolean(attribute="is_system_admin", required=True)


class TenantSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    slug = fields.String(required=True)


class MembershipSchema(Schema):
    id = fields.String(required=True)
    role = fields.String(required=True)
    user = fields.Nested(UserSchema, required=True)
    tenant = fields.Nested(TenantSchema, required=True)


class LoginSchema(Schema):
    tenantSlug = fields.String(required=True)
    identifier = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)


class RefreshSchema(Schema):
    refreshToken = fields.String(required=True, load_only=True)


class LoginResponseSchema(Schema):
    accessToken = fields.String(required=True)
    refreshToken = fields.String(required=True)
    expiresIn = fields.Integer(required=True)
    user = fields.Nested(UserSchema, required=True)
    tenant = fields.Nested(TenantSchema, required=True)
    membershipRole = fields.String(required=True)


class MeResponseSchema(Schema):
    user = fields.Nested(UserSchema, required=True)
    tenant = fields.Nested(TenantSchema, required=True)
    membershipRole = fields.String(required=True)


class SessionSchema(Schema):
    id = fields.String(required=True)
    tenantId = fields.String(attribute="tenant_id", required=True)
    userAgent = fields.String(attribute="user_agent", allow_none=True)
    ipAddress = fields.String(attribute="ip_address", allow_none=True)
    expiresAt = fields.DateTime(attribute="expires_at", required=True)
    createdAt = fields.DateTime(attribute="created_at", required=True)
    lastUsedAt = fields.DateTime(attribute="last_used_at", required=True)
    revokedAt = fields.DateTime(attribute="revoked_at", allow_none=True)


class SessionListSchema(Schema):
    items = fields.List(fields.Nested(SessionSchema), required=True)


class TenantCreateSchema(Schema):
    name = fields.String(required=True)
    slug = fields.String(required=True)


class TenantUpdateSchema(Schema):
    name = fields.String(required=True)


class MemberCreateSchema(Schema):
    email = fields.Email(required=True)
    fullName = fields.String(required=True)
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=8))
    role = fields.String(required=True, validate=validate.OneOf(["owner", "admin", "viewer"]))


class MemberUpdateSchema(Schema):
    role = fields.String(required=True, validate=validate.OneOf(["owner", "admin", "viewer"]))


class MembershipListSchema(Schema):
    items = fields.List(fields.Nested(MembershipSchema), required=True)


class SystemTenantsSchema(Schema):
    items = fields.List(fields.Nested(TenantSchema), required=True)
