from __future__ import annotations

from marshmallow import Schema, fields, validate


class ModelMonitorOverviewItemSchema(Schema):
    metric = fields.String(required=True)
    label = fields.String(required=True)
    value = fields.Float(required=True)
    unit = fields.String(required=True)


class ModelMonitorOverviewResponseSchema(Schema):
    generatedAt = fields.DateTime(required=True)
    items = fields.List(fields.Nested(ModelMonitorOverviewItemSchema), required=True)


class ModelInfoSchema(Schema):
    name = fields.String(required=True)
    parameterSize = fields.String(allow_none=True)
    quantization = fields.String(allow_none=True)
    contextWindow = fields.Integer(allow_none=True)
    memoryBytes = fields.Integer(required=True)
    status = fields.String(required=True)
    lastSeenAt = fields.DateTime(allow_none=True)


class ModelListResponseSchema(Schema):
    generatedAt = fields.DateTime(required=True)
    items = fields.List(fields.Nested(ModelInfoSchema), required=True)


class ModelMonitorSeriesPointSchema(Schema):
    timestamp = fields.DateTime(required=True)
    value = fields.Float(required=True)
    unit = fields.String(required=True)


class ModelMonitorTimeseriesResponseSchema(Schema):
    metric = fields.String(required=True)
    range = fields.String(required=True)
    step = fields.String(required=True)
    series = fields.List(fields.Nested(ModelMonitorSeriesPointSchema), required=True)


class ModelMonitorTimeseriesQuerySchema(Schema):
    metric = fields.String(
        required=True,
        validate=validate.OneOf(
            ["request_rate", "latency", "concurrency", "tokens_per_second", "error_rate", "loaded_models"]
        ),
    )
    range = fields.String(load_default="1h", validate=validate.OneOf(["1h", "6h", "24h"]))
    step = fields.String(load_default="1m", validate=validate.OneOf(["30s", "1m"]))
