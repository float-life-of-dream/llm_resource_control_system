from __future__ import annotations

from app import create_app
from app.extensions.db import db
from app.models import AnalysisSession, AnalysisStatus, Tenant, TenantMembership, TenantRole, User
from app.services.analysis_service import AnalysisExecutionError, AnalysisService
from app.services.auth_service import hash_password


class FakeMonitorService:
    def get_overview(self):
        return {
            "items": [
                {"metric": "cpu", "label": "CPU", "value": 42.5, "unit": "%"},
                {"metric": "gpu", "label": "GPU", "value": 8192, "unit": "MiB"},
            ]
        }

    def get_timeseries(self, metric, range_value, step):
        values = {
            "cpu": [40.0, 45.0, 42.5],
            "gpu": [8000.0, 8192.0, 8100.0],
        }[metric]
        return {
            "metric": metric,
            "range": range_value,
            "step": step,
            "series": [{"timestamp": "2026-04-21T14:01:00Z", "value": value, "unit": "%"} for value in values],
        }


class FakeLogService:
    def search_logs(self, tenant_id, range_value, log_query, limit):
        return [
            {
                "timestamp": "2026-04-21T14:10:00Z",
                "level": "error",
                "service": "worker",
                "message": "timeout failure",
            }
        ]


class FakeOllamaService:
    model = "llama3.1:8b"

    def analyze(self, *, range_value, metrics_snapshot, logs):
        return {
            "summary": "GPU is elevated and timeout failures are increasing.",
            "anomalies": ["GPU usage stayed high."],
            "recommendations": ["Check worker backlog."],
            "rawOutput": '{"summary":"ok"}',
        }


class BrokenOllamaService(FakeOllamaService):
    def analyze(self, *, range_value, metrics_snapshot, logs):
        raise RuntimeError("Ollama request failed")


def make_app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "JWT_SECRET_KEY": "test-secret",
            "BOOTSTRAP_ADMIN_EMAIL": "sysadmin@example.local",
            "BOOTSTRAP_ADMIN_PASSWORD": "ChangeMe123!",
            "BOOTSTRAP_DEFAULT_TENANT_NAME": "System Tenant",
            "BOOTSTRAP_DEFAULT_TENANT_SLUG": "system",
        }
    )
    with app.app_context():
        db.drop_all()
        db.create_all()
        tenant = Tenant(name="Demo Tenant", slug="demo")
        user = User(
            email="viewer@example.local",
            full_name="Viewer User",
            password_hash=hash_password("Password123!"),
        )
        db.session.add_all([tenant, user])
        db.session.flush()
        membership = TenantMembership(tenant_id=tenant.id, user_id=user.id, role=TenantRole.VIEWER)
        db.session.add(membership)
        db.session.commit()
        return app, tenant.id, user.id


def test_analysis_service_persists_completed_result():
    app, tenant_id, user_id = make_app()
    with app.app_context():
        tenant = db.session.get(Tenant, tenant_id)
        user = db.session.get(User, user_id)
        service = AnalysisService(FakeMonitorService(), FakeLogService(), FakeOllamaService(), 50, 200)

        response = service.run_analysis(
            tenant=tenant,
            user=user,
            range_value="1h",
            log_query="timeout",
            log_limit=10,
            include_metrics=True,
        )

        session = db.session.get(AnalysisSession, response["analysisId"])
        assert session is not None
        assert session.status == AnalysisStatus.COMPLETED
        assert session.result.summary.startswith("GPU is elevated")
        assert session.evidence.metrics_snapshot["cpu"]["avg"] == 42.5
        assert response["evidenceSummary"]["logCount"] == 1


def test_analysis_service_marks_failed_sessions():
    app, tenant_id, user_id = make_app()
    with app.app_context():
        tenant = db.session.get(Tenant, tenant_id)
        user = db.session.get(User, user_id)
        service = AnalysisService(FakeMonitorService(), FakeLogService(), BrokenOllamaService(), 50, 200)

        try:
            service.run_analysis(
                tenant=tenant,
                user=user,
                range_value="1h",
                log_query="timeout",
                log_limit=10,
                include_metrics=True,
            )
        except AnalysisExecutionError:
            pass
        else:
            raise AssertionError("Expected analysis to fail")

        failed = AnalysisSession.query.order_by(AnalysisSession.created_at.desc()).first()
        assert failed is not None
        assert failed.status == AnalysisStatus.FAILED
        assert failed.error_message == "Ollama request failed"
