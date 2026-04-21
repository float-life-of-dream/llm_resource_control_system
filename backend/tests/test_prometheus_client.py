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
