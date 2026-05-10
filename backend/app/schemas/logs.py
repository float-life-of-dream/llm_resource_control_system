from __future__ import annotations

from marshmallow import Schema, fields, validate


class LogSearchQuerySchema(Schema):
    range = fields.String(load_default="1h", validate=validate.OneOf(["1h", "6h", "24h"]))
    query = fields.String(load_default="")
    level = fields.String(load_default="", validate=validate.OneOf(["", "error", "warn", "warning", "info", "debug"]))
    service = fields.String(load_default="")
    limit = fields.Integer(load_default=100, validate=validate.Range(min=1, max=500))


class LogSummaryQuerySchema(Schema):
    range = fields.String(load_default="1h", validate=validate.OneOf(["1h", "6h", "24h"]))
    query = fields.String(load_default="")


class LogServicesQuerySchema(Schema):
    range = fields.String(load_default="24h", validate=validate.OneOf(["1h", "6h", "24h"]))


class LogItemSchema(Schema):
    timestamp = fields.String(required=True)
    level = fields.String(required=True)
    service = fields.String(required=True)
    message = fields.String(required=True)
    traceId = fields.String(required=True)
    host = fields.String(required=True)
    source = fields.String(required=True)


class LogSearchResponseSchema(Schema):
    generatedAt = fields.DateTime(required=True)
    range = fields.String(required=True)
    total = fields.Integer(required=True)
    items = fields.List(fields.Nested(LogItemSchema), required=True)


class LogBucketSchema(Schema):
    key = fields.String(required=True)
    count = fields.Integer(required=True)


class LogSummaryResponseSchema(Schema):
    generatedAt = fields.DateTime(required=True)
    total = fields.Integer(required=True)
    levels = fields.List(fields.Nested(LogBucketSchema), required=True)
    services = fields.List(fields.Nested(LogBucketSchema), required=True)


class LogServicesResponseSchema(Schema):
    generatedAt = fields.DateTime(required=True)
    items = fields.List(fields.String(), required=True)
