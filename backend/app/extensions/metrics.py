from __future__ import annotations

from time import perf_counter

from flask import Response, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest


HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests processed by the backend.",
    ["method", "endpoint", "status"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "endpoint"],
)
ANALYSIS_RUN_TOTAL = Counter(
    "analysis_run_total",
    "Total analysis run attempts.",
)
ANALYSIS_RUN_FAILED_TOTAL = Counter(
    "analysis_run_failed_total",
    "Total failed analysis runs.",
)
OLLAMA_REQUEST_DURATION_SECONDS = Histogram(
    "ollama_request_duration_seconds",
    "Duration of Ollama requests in seconds.",
)
ELASTICSEARCH_QUERY_DURATION_SECONDS = Histogram(
    "elasticsearch_query_duration_seconds",
    "Duration of Elasticsearch log queries in seconds.",
)


def instrument_app(app):
    @app.before_request
    def _before_request():
        request._metrics_started_at = perf_counter()

    @app.after_request
    def _after_request(response):
        started_at = getattr(request, "_metrics_started_at", None)
        endpoint = request.endpoint or "unknown"
        if started_at is not None:
            HTTP_REQUEST_DURATION_SECONDS.labels(request.method, endpoint).observe(perf_counter() - started_at)
        HTTP_REQUESTS_TOTAL.labels(request.method, endpoint, response.status_code).inc()
        return response

    @app.get("/metrics")
    def metrics():
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


def record_analysis_run(success: bool):
    ANALYSIS_RUN_TOTAL.inc()
    if not success:
        ANALYSIS_RUN_FAILED_TOTAL.inc()
