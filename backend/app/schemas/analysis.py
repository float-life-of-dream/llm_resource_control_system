from __future__ import annotations

from marshmallow import Schema, fields, validate

from app.schemas.auth import TenantSchema, UserSchema


class AnalysisRunSchema(Schema):
    range = fields.String(required=True, validate=validate.OneOf(["1h", "6h", "24h"]))
    logQuery = fields.String(load_default="", allow_none=True)
    logLimit = fields.Integer(load_default=50, validate=validate.Range(min=1, max=1000))
    includeMetrics = fields.Boolean(load_default=True)


class AnalysisEvidenceSummarySchema(Schema):
    metrics = fields.List(fields.String(), required=True)
    logCount = fields.Integer(required=True)


class AnalysisRunResponseSchema(Schema):
    analysisId = fields.String(required=True)
    status = fields.String(required=True)
    summary = fields.String(required=True)
    anomalies = fields.List(fields.String(), required=True)
    recommendations = fields.List(fields.String(), required=True)
    evidenceSummary = fields.Nested(AnalysisEvidenceSummarySchema, required=True)
    model = fields.String(required=True)
    durationMs = fields.Integer(required=True)


class AnalysisHistoryItemSchema(Schema):
    analysisId = fields.String(attribute="id", required=True)
    status = fields.Method("get_status")
    range = fields.String(attribute="range_value", required=True)
    logQuery = fields.String(attribute="log_query", allow_none=True)
    logLimit = fields.Integer(attribute="log_limit", required=True)
    includeMetrics = fields.Boolean(attribute="include_metrics", required=True)
    model = fields.String(attribute="model_name", required=True)
    durationMs = fields.Integer(attribute="duration_ms", allow_none=True)
    errorMessage = fields.String(attribute="error_message", allow_none=True)
    createdAt = fields.DateTime(attribute="created_at", required=True)
    completedAt = fields.DateTime(attribute="completed_at", allow_none=True)
    summary = fields.Method("get_summary")
    evidenceSummary = fields.Method("get_evidence_summary")

    def get_summary(self, obj):
        return obj.result.summary if obj.result and obj.result.summary else ""

    def get_status(self, obj):
        return obj.status.value

    def get_evidence_summary(self, obj):
        metrics = sorted((obj.evidence.metrics_snapshot or {}).keys()) if obj.evidence else []
        log_count = len(obj.evidence.log_excerpt or []) if obj.evidence else 0
        return {"metrics": metrics, "logCount": log_count}


class AnalysisHistoryListSchema(Schema):
    items = fields.List(fields.Nested(AnalysisHistoryItemSchema), required=True)


class AnalysisEvidenceSchema(Schema):
    metricsSnapshot = fields.Dict(attribute="metrics_snapshot", required=True)
    logExcerpt = fields.List(fields.Dict(), attribute="log_excerpt", required=True)


class AnalysisDetailSchema(Schema):
    analysisId = fields.String(attribute="id", required=True)
    status = fields.Method("get_status")
    range = fields.String(attribute="range_value", required=True)
    logQuery = fields.String(attribute="log_query", allow_none=True)
    logLimit = fields.Integer(attribute="log_limit", required=True)
    includeMetrics = fields.Boolean(attribute="include_metrics", required=True)
    model = fields.String(attribute="model_name", required=True)
    durationMs = fields.Integer(attribute="duration_ms", allow_none=True)
    errorMessage = fields.String(attribute="error_message", allow_none=True)
    createdAt = fields.DateTime(attribute="created_at", required=True)
    completedAt = fields.DateTime(attribute="completed_at", allow_none=True)
    summary = fields.Method("get_summary")
    anomalies = fields.Method("get_anomalies")
    recommendations = fields.Method("get_recommendations")
    rawModelOutput = fields.Method("get_raw_output")
    user = fields.Nested(UserSchema, required=True)
    tenant = fields.Nested(TenantSchema, required=True)
    evidence = fields.Nested(AnalysisEvidenceSchema, attribute="evidence", required=True)

    def get_summary(self, obj):
        return obj.result.summary if obj.result and obj.result.summary else ""

    def get_status(self, obj):
        return obj.status.value

    def get_anomalies(self, obj):
        return obj.result.anomalies if obj.result and obj.result.anomalies else []

    def get_recommendations(self, obj):
        return obj.result.recommendations if obj.result and obj.result.recommendations else []

    def get_raw_output(self, obj):
        return obj.result.raw_model_output if obj.result else ""
