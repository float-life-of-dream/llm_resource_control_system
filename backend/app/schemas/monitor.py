from __future__ import annotations

from marshmallow import Schema, fields, validate


class HealthSchema(Schema):
    status = fields.String(required=True)
    service = fields.String(required=True)
    version = fields.String(required=True)


class OverviewItemSchema(Schema):
    metric = fields.String(required=True)
    label = fields.String(required=True)
    value = fields.Float(required=True)
    unit = fields.String(required=True)


class OverviewResponseSchema(Schema):
    generatedAt = fields.DateTime(required=True)
    items = fields.List(fields.Nested(OverviewItemSchema), required=True)


class SeriesPointSchema(Schema):
    timestamp = fields.DateTime(required=True)
    value = fields.Float(required=True)
    unit = fields.String(required=True)


class TimeseriesResponseSchema(Schema):
    metric = fields.String(required=True)
    range = fields.String(required=True)
    step = fields.String(required=True)
    series = fields.List(fields.Nested(SeriesPointSchema), required=True)


class TimeseriesQuerySchema(Schema):
    metric = fields.String(
        required=True,
        validate=validate.OneOf(
            [
                "cpu",
                "memory",
                "disk",
                "gpu",
                "gpu_memory_used",
                "gpu_memory_utilization",
                "gpu_utilization",
                "gpu_temperature",
                "gpu_power_usage",
            ]
        ),
    )
    range = fields.String(load_default="1h", validate=validate.OneOf(["1h", "6h", "24h"]))
    step = fields.String(load_default="1m", validate=validate.OneOf(["30s", "1m"]))
