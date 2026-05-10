from __future__ import annotations

from marshmallow import Schema, fields, validate


class ChatSessionCreateSchema(Schema):
    model = fields.String(load_default="")
    title = fields.String(load_default="", validate=validate.Length(max=160))


class ChatSessionSchema(Schema):
    id = fields.String(required=True)
    title = fields.String(required=True)
    model = fields.String(required=True)
    createdAt = fields.DateTime(attribute="created_at", required=True)
    updatedAt = fields.DateTime(attribute="updated_at", required=True)


class ChatSessionListSchema(Schema):
    items = fields.List(fields.Nested(ChatSessionSchema), required=True)


class ChatMessageSchema(Schema):
    id = fields.String(required=True)
    role = fields.Method("get_role", required=True)
    content = fields.String(required=True)
    rawMetadata = fields.Dict(attribute="raw_metadata", required=True)
    createdAt = fields.DateTime(attribute="created_at", required=True)

    def get_role(self, obj):
        return obj.role.value if hasattr(obj.role, "value") else str(obj.role)


class ChatSessionDetailSchema(Schema):
    session = fields.Nested(ChatSessionSchema, required=True)
    messages = fields.List(fields.Nested(ChatMessageSchema), required=True)


class ChatMessageCreateSchema(Schema):
    message = fields.String(required=True, validate=validate.Length(min=1, max=8000))
