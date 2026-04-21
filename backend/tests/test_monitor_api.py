from unittest.mock import patch

from app import create_app


def test_health_endpoint():
    app = create_app()
    client = app.test_client()

    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"


def test_overview_endpoint():
    app = create_app()
    client = app.test_client()

    with patch("app.api.monitor._build_service") as service_factory:
        service_factory.return_value.get_overview.return_value = {
            "generatedAt": "2026-04-21T15:00:00+00:00",
            "items": [{"metric": "cpu", "label": "CPU", "value": 42.5, "unit": "%"}],
        }

        response = client.get("/api/monitor/overview")

    assert response.status_code == 200
    assert response.get_json()["items"][0]["metric"] == "cpu"


def test_timeseries_endpoint():
    app = create_app()
    client = app.test_client()

    with patch("app.api.monitor._build_service") as service_factory:
        service_factory.return_value.get_timeseries.return_value = {
            "metric": "gpu",
            "range": "1h",
            "step": "1m",
            "series": [{"timestamp": "2026-04-21T14:01:00+00:00", "value": 8192, "unit": "MiB"}],
        }

        response = client.get("/api/monitor/timeseries?metric=gpu&range=1h&step=1m")

    assert response.status_code == 200
    assert response.get_json()["metric"] == "gpu"
