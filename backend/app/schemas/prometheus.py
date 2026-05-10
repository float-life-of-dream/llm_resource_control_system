from __future__ import annotations

from marshmallow import Schema, fields


class PrometheusHealthResponseSchema(Schema):
    status = fields.String(required=True)
    baseUrl = fields.String(required=True)
    generatedAt = fields.DateTime(required=True)


class PrometheusTargetSchema(Schema):
    job = fields.String(required=True)
    instance = fields.String(required=True)
    health = fields.String(required=True)
    scrapeUrl = fields.String(required=True)
    lastScrape = fields.DateTime(allow_none=True)
    lastError = fields.String(required=True)


class PrometheusTargetsResponseSchema(Schema):
    generatedAt = fields.DateTime(required=True)
    items = fields.List(fields.Nested(PrometheusTargetSchema), required=True)


class PrometheusMetricSchema(Schema):
    key = fields.String(required=True)
    label = fields.String(required=True)
    unit = fields.String(required=True)


class PrometheusMetricGroupSchema(Schema):
    key = fields.String(required=True)
    label = fields.String(required=True)
    items = fields.List(fields.Nested(PrometheusMetricSchema), required=True)


class PrometheusMetricsResponseSchema(Schema):
    generatedAt = fields.DateTime(required=True)
    groups = fields.List(fields.Nested(PrometheusMetricGroupSchema), required=True)
