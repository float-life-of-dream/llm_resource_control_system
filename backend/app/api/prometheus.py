from __future__ import annotations

from flask import current_app
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from app.models import TenantRole
from app.schemas.prometheus import (
    PrometheusHealthResponseSchema,
    PrometheusMetricsResponseSchema,
    PrometheusTargetsResponseSchema,
)
from app.security import role_required
from app.services.prometheus_client import PrometheusClient, PrometheusClientError
from app.services.prometheus_status_service import PrometheusStatusService

blp = Blueprint("prometheus", __name__, url_prefix="/api/prometheus", description="Prometheus status APIs")


def _build_service() -> PrometheusStatusService:
    client = PrometheusClient(
        current_app.config["PROMETHEUS_BASE_URL"],
        timeout=current_app.config["PROMETHEUS_TIMEOUT"],
    )
    return PrometheusStatusService(client)


@blp.route("/health")
class PrometheusHealthResource(MethodView):
    @role_required(TenantRole.OWNER, TenantRole.ADMIN, TenantRole.VIEWER)
    @blp.response(200, PrometheusHealthResponseSchema)
    def get(self):
        try:
            return _build_service().get_health()
        except PrometheusClientError as exc:
            abort(502, message=str(exc))


@blp.route("/targets")
class PrometheusTargetsResource(MethodView):
    @role_required(TenantRole.OWNER, TenantRole.ADMIN, TenantRole.VIEWER)
    @blp.response(200, PrometheusTargetsResponseSchema)
    def get(self):
        try:
            return _build_service().get_targets()
        except PrometheusClientError as exc:
            abort(502, message=str(exc))


@blp.route("/metrics")
class PrometheusMetricsResource(MethodView):
    @role_required(TenantRole.OWNER, TenantRole.ADMIN, TenantRole.VIEWER)
    @blp.response(200, PrometheusMetricsResponseSchema)
    def get(self):
        return _build_service().get_metrics()
