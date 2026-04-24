from __future__ import annotations

from typing import Any

from flask import current_app
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from app.schemas.monitor import (
    OverviewResponseSchema,
    TimeseriesQuerySchema,
    TimeseriesResponseSchema,
)
from app.services.monitor_service import MonitorService
from app.services.prometheus_client import PrometheusClient, PrometheusClientError

blp = Blueprint("monitor", __name__, url_prefix="/api/monitor", description="Monitor APIs")


def _build_service() -> MonitorService:
    client = PrometheusClient(
        current_app.config["PROMETHEUS_BASE_URL"],
        timeout=current_app.config["PROMETHEUS_TIMEOUT"],
    )
    return MonitorService(client)


@blp.route("/overview")
class OverviewResource(MethodView):
    @blp.response(200, OverviewResponseSchema)
    def get(self) -> dict[str, Any]:
        try:
            return _build_service().get_overview()
        except PrometheusClientError as exc:
            abort(502, message=str(exc))


@blp.route("/timeseries")
class TimeseriesResource(MethodView):
    @blp.arguments(TimeseriesQuerySchema, location="query")
    @blp.response(200, TimeseriesResponseSchema)
    def get(self, args: dict[str, Any]) -> dict[str, Any]:
        try:
            return _build_service().get_timeseries(args["metric"], args["range"], args["step"])
        except PrometheusClientError as exc:
            abort(502, message=str(exc))

