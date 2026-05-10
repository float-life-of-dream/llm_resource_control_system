from __future__ import annotations

from flask import current_app
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from app.models import TenantRole
from app.schemas.model_monitor import (
    ModelListResponseSchema,
    ModelMonitorOverviewResponseSchema,
    ModelMonitorTimeseriesQuerySchema,
    ModelMonitorTimeseriesResponseSchema,
)
from app.security import role_required
from app.services.model_monitor_service import ModelMonitorService
from app.services.prometheus_client import PrometheusClient, PrometheusClientError

blp = Blueprint("model_monitor", __name__, url_prefix="/api/model-monitor", description="Model monitor APIs")


def _build_service() -> ModelMonitorService:
    client = PrometheusClient(
        current_app.config["PROMETHEUS_BASE_URL"],
        timeout=current_app.config["PROMETHEUS_TIMEOUT"],
    )
    return ModelMonitorService(client)


@blp.route("/overview")
class ModelMonitorOverviewResource(MethodView):
    @role_required(TenantRole.OWNER, TenantRole.ADMIN, TenantRole.VIEWER)
    @blp.response(200, ModelMonitorOverviewResponseSchema)
    def get(self):
        try:
            return _build_service().get_overview()
        except PrometheusClientError as exc:
            abort(502, message=str(exc))


@blp.route("/models")
class ModelListResource(MethodView):
    @role_required(TenantRole.OWNER, TenantRole.ADMIN, TenantRole.VIEWER)
    @blp.response(200, ModelListResponseSchema)
    def get(self):
        try:
            return _build_service().get_models()
        except PrometheusClientError as exc:
            abort(502, message=str(exc))


@blp.route("/timeseries")
class ModelMonitorTimeseriesResource(MethodView):
    @role_required(TenantRole.OWNER, TenantRole.ADMIN, TenantRole.VIEWER)
    @blp.arguments(ModelMonitorTimeseriesQuerySchema, location="query")
    @blp.response(200, ModelMonitorTimeseriesResponseSchema)
    def get(self, args):
        try:
            return _build_service().get_timeseries(args["metric"], args["range"], args["step"])
        except PrometheusClientError as exc:
            abort(502, message=str(exc))
