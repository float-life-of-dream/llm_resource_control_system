from __future__ import annotations

from flask import current_app, g
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from app.models import TenantRole
from app.schemas.analysis import (
    AnalysisDetailSchema,
    AnalysisHistoryListSchema,
    AnalysisRunResponseSchema,
    AnalysisRunSchema,
)
from app.security import role_required
from app.services.analysis_service import AnalysisExecutionError, AnalysisService
from app.services.elasticsearch_log_service import ElasticsearchLogService
from app.services.monitor_service import MonitorService
from app.services.ollama_analysis_service import OllamaAnalysisService
from app.services.prometheus_client import PrometheusClient

blp = Blueprint("analysis", __name__, url_prefix="/api/analysis", description="AI analysis APIs")


def _build_service() -> AnalysisService:
    monitor_service = MonitorService(
        PrometheusClient(
            current_app.config["PROMETHEUS_BASE_URL"],
            timeout=current_app.config["PROMETHEUS_TIMEOUT"],
        )
    )
    log_service = ElasticsearchLogService(
        current_app.config["ELASTICSEARCH_BASE_URL"],
        current_app.config["ELASTICSEARCH_INDEX"],
        username=current_app.config["ELASTICSEARCH_USERNAME"],
        password=current_app.config["ELASTICSEARCH_PASSWORD"],
        timeout=current_app.config["ELASTICSEARCH_TIMEOUT"],
    )
    ollama_service = OllamaAnalysisService(
        current_app.config["OLLAMA_BASE_URL"],
        current_app.config["OLLAMA_MODEL"],
        timeout=current_app.config["OLLAMA_TIMEOUT"],
    )
    return AnalysisService(
        monitor_service,
        log_service,
        ollama_service,
        log_limit_default=current_app.config["ANALYSIS_LOG_LIMIT_DEFAULT"],
        log_limit_max=current_app.config["ANALYSIS_LOG_LIMIT_MAX"],
    )


@blp.route("/run")
class AnalysisRunResource(MethodView):
    @role_required(TenantRole.OWNER, TenantRole.ADMIN, TenantRole.VIEWER)
    @blp.arguments(AnalysisRunSchema)
    @blp.response(200, AnalysisRunResponseSchema)
    def post(self, args):
        try:
            return _build_service().run_analysis(
                tenant=g.current_tenant,
                user=g.current_user,
                range_value=args["range"],
                log_query=args.get("logQuery") or "",
                log_limit=args.get("logLimit"),
                include_metrics=args.get("includeMetrics", True),
            )
        except AnalysisExecutionError as exc:
            abort(exc.status_code, message=str(exc))


@blp.route("/history")
class AnalysisHistoryResource(MethodView):
    @role_required(TenantRole.OWNER, TenantRole.ADMIN, TenantRole.VIEWER)
    @blp.response(200, AnalysisHistoryListSchema)
    def get(self):
        return _build_service().list_history(g.current_tenant.id)


@blp.route("/history/<analysis_id>")
class AnalysisHistoryDetailResource(MethodView):
    @role_required(TenantRole.OWNER, TenantRole.ADMIN, TenantRole.VIEWER)
    @blp.response(200, AnalysisDetailSchema)
    def get(self, analysis_id: str):
        try:
            return _build_service().get_detail(g.current_tenant.id, analysis_id)
        except LookupError as exc:
            abort(404, message=str(exc))
