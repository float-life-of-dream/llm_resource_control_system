from __future__ import annotations

from typing import Any

from flask.views import MethodView
from flask_smorest import Blueprint

from app.schemas.monitor import HealthSchema

blp = Blueprint("health", __name__, url_prefix="/api", description="Health checks")


@blp.route("/health")
class HealthResource(MethodView):
    @blp.response(200, HealthSchema)
    def get(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "service": "ai-monitor-backend",
            "version": "0.1.0",
        }

