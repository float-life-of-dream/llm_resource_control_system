from __future__ import annotations

from datetime import UTC, datetime

from flask import current_app, g
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from app.models import TenantRole
from app.schemas.logs import (
    LogSearchQuerySchema,
    LogSearchResponseSchema,
    LogServicesQuerySchema,
    LogServicesResponseSchema,
    LogSummaryQuerySchema,
    LogSummaryResponseSchema,
)
from app.security import role_required
from app.services.elasticsearch_log_service import ElasticsearchLogError, ElasticsearchLogService

blp = Blueprint("logs", __name__, url_prefix="/api/logs", description="Tenant log search APIs")


def _build_service() -> ElasticsearchLogService:
    return ElasticsearchLogService(
        current_app.config["ELASTICSEARCH_BASE_URL"],
        current_app.config["ELASTICSEARCH_INDEX"],
        username=current_app.config["ELASTICSEARCH_USERNAME"],
        password=current_app.config["ELASTICSEARCH_PASSWORD"],
        timeout=current_app.config["ELASTICSEARCH_TIMEOUT"],
    )


def _normalize_level(level: str) -> str:
    if level == "warning":
        return "warn"
    return level


@blp.route("/search")
class LogSearchResource(MethodView):
    @role_required(TenantRole.OWNER, TenantRole.ADMIN, TenantRole.VIEWER)
    @blp.arguments(LogSearchQuerySchema, location="query")
    @blp.response(200, LogSearchResponseSchema)
    def get(self, args):
        try:
            result = _build_service().search_log_page(
                tenant_id=g.current_tenant.id,
                range_value=args["range"],
                log_query=args.get("query") or "",
                level=_normalize_level(args.get("level") or "") or None,
                service=args.get("service") or None,
                limit=args["limit"],
            )
        except ElasticsearchLogError as exc:
            abort(502, message=str(exc))

        return {
            "generatedAt": datetime.now(UTC),
            "range": args["range"],
            "total": result["total"],
            "items": result["items"],
        }


@blp.route("/summary")
class LogSummaryResource(MethodView):
    @role_required(TenantRole.OWNER, TenantRole.ADMIN, TenantRole.VIEWER)
    @blp.arguments(LogSummaryQuerySchema, location="query")
    @blp.response(200, LogSummaryResponseSchema)
    def get(self, args):
        try:
            summary = _build_service().get_summary(
                tenant_id=g.current_tenant.id,
                range_value=args["range"],
                log_query=args.get("query") or "",
            )
        except ElasticsearchLogError as exc:
            abort(502, message=str(exc))

        return {"generatedAt": datetime.now(UTC), **summary}


@blp.route("/services")
class LogServicesResource(MethodView):
    @role_required(TenantRole.OWNER, TenantRole.ADMIN, TenantRole.VIEWER)
    @blp.arguments(LogServicesQuerySchema, location="query")
    @blp.response(200, LogServicesResponseSchema)
    def get(self, args):
        try:
            services = _build_service().get_services(g.current_tenant.id, args["range"])
        except ElasticsearchLogError as exc:
            abort(502, message=str(exc))

        return {"generatedAt": datetime.now(UTC), "items": services}
