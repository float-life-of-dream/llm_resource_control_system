from unittest.mock import Mock, patch

import pytest
import requests

from app.services.prometheus_client import PrometheusClient, PrometheusClientError


def test_query_success():
    response = Mock()
    response.json.return_value = {"status": "success", "data": {"result": []}}
    response.raise_for_status.return_value = None

    with patch("app.services.prometheus_client.requests.get", return_value=response):
        client = PrometheusClient("http://prometheus")
        assert client.query("up") == {"result": []}


def test_query_timeout():
    with patch("app.services.prometheus_client.requests.get", side_effect=requests.Timeout):
        client = PrometheusClient("http://prometheus")
        with pytest.raises(PrometheusClientError, match="timed out"):
            client.query("up")


def test_query_error_payload():
    response = Mock()
    response.json.return_value = {"status": "error", "error": "bad query"}
    response.raise_for_status.return_value = None

    with patch("app.services.prometheus_client.requests.get", return_value=response):
        client = PrometheusClient("http://prometheus")
        with pytest.raises(PrometheusClientError, match="bad query"):
            client.query("up")


def test_query_range_success():
    response = Mock()
    response.json.return_value = {
        "status": "success",
        "data": {"resultType": "matrix", "result": [{"metric": {}, "values": [[1713744000, "42.5"]]}]},
    }
    response.raise_for_status.return_value = None

    with patch("app.services.prometheus_client.requests.get", return_value=response):
        client = PrometheusClient("http://prometheus")
        result = client.query_range("up", "2026-04-22T00:00:00+00:00", "2026-04-22T01:00:00+00:00", "1m")

    assert result["resultType"] == "matrix"


def test_targets_success():
    response = Mock()
    response.json.return_value = {"status": "success", "data": {"activeTargets": []}}
    response.raise_for_status.return_value = None

    with patch("app.services.prometheus_client.requests.get", return_value=response):
        client = PrometheusClient("http://prometheus")
        assert client.targets() == {"activeTargets": []}


def test_health_success():
    response = Mock()
    response.json.return_value = {"status": "success", "data": {"startTime": "2026-04-30T00:00:00Z"}}
    response.raise_for_status.return_value = None

    with patch("app.services.prometheus_client.requests.get", return_value=response):
        client = PrometheusClient("http://prometheus")
        assert client.health()["startTime"] == "2026-04-30T00:00:00Z"
