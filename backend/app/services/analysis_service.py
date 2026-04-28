from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter

from app.extensions.db import db
from app.models import AnalysisEvidence, AnalysisResult, AnalysisSession, AnalysisStatus


class AnalysisExecutionError(RuntimeError):
    status_code = 502


METRIC_THRESHOLDS = {
    "cpu": 85.0,
    "memory": 24.0,
    "disk": 85.0,
    "gpu": 12288.0,
}


class AnalysisService:
    def __init__(self, monitor_service, log_service, ollama_service, log_limit_default: int, log_limit_max: int):
        self.monitor_service = monitor_service
        self.log_service = log_service
        self.ollama_service = ollama_service
        self.log_limit_default = log_limit_default
        self.log_limit_max = log_limit_max

    def run_analysis(self, *, tenant, user, range_value: str, log_query: str, log_limit: int | None, include_metrics: bool):
        effective_limit = max(1, min(log_limit or self.log_limit_default, self.log_limit_max))
        session = AnalysisSession(
            tenant_id=tenant.id,
            user_id=user.id,
            range_value=range_value,
            log_query=log_query or "",
            log_limit=effective_limit,
            include_metrics=include_metrics,
            status=AnalysisStatus.PENDING,
            model_name=self.ollama_service.model,
        )
        db.session.add(session)
        db.session.flush()

        metrics_snapshot: dict = {}
        logs: list[dict] = []
        started_at = perf_counter()

        try:
            if include_metrics:
                metrics_snapshot = self._build_metrics_snapshot(range_value)
            logs = self.log_service.search_logs(tenant.id, range_value, log_query or "", effective_limit)
            evidence = AnalysisEvidence(
                analysis_session_id=session.id,
                metrics_snapshot=metrics_snapshot,
                log_excerpt=logs,
            )
            db.session.add(evidence)
            db.session.flush()

            analysis = self.ollama_service.analyze(
                range_value=range_value,
                metrics_snapshot=metrics_snapshot,
                logs=logs,
            )
            duration_ms = int((perf_counter() - started_at) * 1000)
            session.status = AnalysisStatus.COMPLETED
            session.duration_ms = duration_ms
            session.completed_at = datetime.now(UTC)
            result = AnalysisResult(
                analysis_session_id=session.id,
                summary=analysis["summary"],
                anomalies=analysis["anomalies"],
                recommendations=analysis["recommendations"],
                raw_model_output=analysis["rawOutput"],
                risk_metadata={"logCount": len(logs), "metricCount": len(metrics_snapshot)},
            )
            db.session.add(result)
            db.session.commit()
            db.session.refresh(session)
            return self._serialize_run_response(session)
        except Exception as exc:
            raw_output = getattr(exc, "raw_output", "")
            duration_ms = int((perf_counter() - started_at) * 1000)
            session.status = AnalysisStatus.FAILED
            session.duration_ms = duration_ms
            session.completed_at = datetime.now(UTC)
            session.error_message = str(exc)
            if session.evidence is None:
                db.session.add(
                    AnalysisEvidence(
                        analysis_session_id=session.id,
                        metrics_snapshot=metrics_snapshot,
                        log_excerpt=logs,
                    )
                )
            if session.result is None:
                db.session.add(
                    AnalysisResult(
                        analysis_session_id=session.id,
                        summary="",
                        anomalies=[],
                        recommendations=[],
                        raw_model_output=raw_output,
                        risk_metadata={"logCount": len(logs), "metricCount": len(metrics_snapshot)},
                    )
                )
            db.session.commit()
            raise AnalysisExecutionError(str(exc)) from exc

    def list_history(self, tenant_id: str):
        items = (
            AnalysisSession.query.filter_by(tenant_id=tenant_id)
            .order_by(AnalysisSession.created_at.desc())
            .limit(20)
            .all()
        )
        return {"items": items}

    def get_detail(self, tenant_id: str, analysis_id: str):
        session = AnalysisSession.query.filter_by(id=analysis_id, tenant_id=tenant_id).first()
        if session is None:
            raise LookupError("Analysis record not found")
        return session

    def _build_metrics_snapshot(self, range_value: str) -> dict:
        overview = self.monitor_service.get_overview()
        summary: dict = {}
        for item in overview["items"]:
            metric = item["metric"]
            timeseries = self.monitor_service.get_timeseries(metric, range_value, "1m")
            values = [point["value"] for point in timeseries["series"]]
            current = round(item["value"], 2)
            summary[metric] = {
                "label": item["label"],
                "unit": item["unit"],
                "current": current,
                "min": round(min(values), 2) if values else current,
                "max": round(max(values), 2) if values else current,
                "avg": round(sum(values) / len(values), 2) if values else current,
                "threshold": METRIC_THRESHOLDS.get(metric),
                "thresholdExceeded": bool(METRIC_THRESHOLDS.get(metric) is not None and current >= METRIC_THRESHOLDS[metric]),
            }
        return summary

    @staticmethod
    def _serialize_run_response(session: AnalysisSession) -> dict:
        metrics = sorted((session.evidence.metrics_snapshot or {}).keys()) if session.evidence else []
        log_count = len(session.evidence.log_excerpt or []) if session.evidence else 0
        return {
            "analysisId": session.id,
            "status": session.status.value,
            "summary": session.result.summary if session.result else "",
            "anomalies": session.result.anomalies if session.result else [],
            "recommendations": session.result.recommendations if session.result else [],
            "evidenceSummary": {"metrics": metrics, "logCount": log_count},
            "model": session.model_name,
            "durationMs": session.duration_ms or 0,
        }
