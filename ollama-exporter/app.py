from __future__ import annotations

import json
import os
import re
from time import perf_counter
from typing import Any

import requests
from flask import Flask, Response, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, Histogram, generate_latest


TARGET_URL = os.getenv("OLLAMA_EXPORTER_TARGET_URL", "http://host.docker.internal:11434").rstrip("/")
TIMEOUT = float(os.getenv("OLLAMA_EXPORTER_TIMEOUT", "10"))
PORT = int(os.getenv("OLLAMA_EXPORTER_PORT", "9500"))

app = Flask(__name__)
registry = CollectorRegistry()

loaded_models = Gauge("ollama_loaded_models", "Current number of loaded Ollama models.", registry=registry)
model_memory_bytes = Gauge(
    "ollama_model_memory_bytes",
    "Memory used by a loaded Ollama model.",
    ["model"],
    registry=registry,
)
model_context_window = Gauge(
    "ollama_model_context_window",
    "Context window configured for a loaded Ollama model.",
    ["model"],
    registry=registry,
)
model_quantization_info = Gauge(
    "ollama_model_quantization_info",
    "Loaded Ollama model metadata.",
    ["model", "parameter_size", "quantization"],
    registry=registry,
)
requests_total = Counter(
    "ollama_requests_total",
    "Ollama inference requests proxied through this exporter.",
    ["endpoint", "status"],
    registry=registry,
)
request_duration_seconds = Histogram(
    "ollama_request_duration_seconds",
    "Duration of Ollama inference requests proxied through this exporter.",
    ["endpoint"],
    registry=registry,
)
active_requests = Gauge(
    "ollama_active_requests",
    "Active Ollama inference requests proxied through this exporter.",
    registry=registry,
)
tokens_per_second = Gauge(
    "ollama_tokens_per_second",
    "Last observed generated tokens per second from proxied Ollama responses.",
    ["endpoint"],
    registry=registry,
)
scrape_errors = Counter(
    "ollama_exporter_scrape_errors_total",
    "Errors while scraping Ollama model metadata.",
    registry=registry,
)


def _ollama_get(path: str, **kwargs):
    return requests.get(f"{TARGET_URL}{path}", timeout=TIMEOUT, **kwargs)


def _ollama_post(path: str, **kwargs):
    return requests.post(f"{TARGET_URL}{path}", timeout=None, **kwargs)


def _extract_context_window(payload: dict[str, Any]) -> int:
    parameters = payload.get("parameters") or ""
    match = re.search(r"(?:num_ctx|context_length)\s+(\d+)", parameters)
    if match:
        return int(match.group(1))
    details = payload.get("details") or {}
    for key in ("context_length", "num_ctx"):
        if details.get(key):
            return int(details[key])
    return 0


def _model_name(item: dict[str, Any]) -> str:
    return item.get("model") or item.get("name") or "unknown"


def _model_memory(item: dict[str, Any]) -> int:
    return int(item.get("size_vram") or item.get("size") or 0)


def collect_model_metadata() -> None:
    model_memory_bytes._metrics.clear()
    model_context_window._metrics.clear()
    model_quantization_info._metrics.clear()
    try:
        ps_response = _ollama_get("/api/ps")
        ps_response.raise_for_status()
        models = ps_response.json().get("models", [])
        loaded_models.set(len(models))

        for item in models:
            name = _model_name(item)
            model_memory_bytes.labels(name).set(_model_memory(item))

            show_response = _ollama_post("/api/show", json={"model": name})
            show_response.raise_for_status()
            show_payload = show_response.json()
            details = show_payload.get("details") or {}
            parameter_size = details.get("parameter_size") or "unknown"
            quantization = details.get("quantization_level") or "unknown"
            context_window = _extract_context_window(show_payload)

            model_context_window.labels(name).set(context_window)
            model_quantization_info.labels(name, parameter_size, quantization).set(1)
    except requests.RequestException:
        loaded_models.set(0)
        scrape_errors.inc()


def _token_rate(payload: dict[str, Any]) -> float:
    eval_count = float(payload.get("eval_count") or 0)
    eval_duration_ns = float(payload.get("eval_duration") or 0)
    if eval_count <= 0 or eval_duration_ns <= 0:
        return 0.0
    return eval_count / (eval_duration_ns / 1_000_000_000)


def _proxy_stream(endpoint: str, payload: dict[str, Any]):
    started_at = perf_counter()
    active_requests.inc()
    status = "success"

    try:
        upstream = _ollama_post(f"/api/{endpoint}", json=payload, stream=True)
        upstream.raise_for_status()
    except requests.RequestException as exc:
        active_requests.dec()
        requests_total.labels(endpoint, "error").inc()
        request_duration_seconds.labels(endpoint).observe(perf_counter() - started_at)
        return jsonify({"error": str(exc)}), 502

    def generate():
        nonlocal status
        last_payload = {}
        try:
            for line in upstream.iter_lines():
                if not line:
                    continue
                yield line + b"\n"
                try:
                    last_payload = json.loads(line.decode("utf-8"))
                except json.JSONDecodeError:
                    status = "parse_error"
            rate = _token_rate(last_payload)
            if rate:
                tokens_per_second.labels(endpoint).set(rate)
        finally:
            active_requests.dec()
            requests_total.labels(endpoint, status).inc()
            request_duration_seconds.labels(endpoint).observe(perf_counter() - started_at)
            upstream.close()

    return Response(generate(), mimetype="application/x-ndjson")


@app.get("/health")
def health():
    return {"status": "ok", "target": TARGET_URL}


@app.get("/metrics")
def metrics():
    collect_model_metadata()
    return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)


@app.post("/api/generate")
def generate():
    return _proxy_stream("generate", request.get_json(silent=True) or {})


@app.post("/api/chat")
def chat():
    return _proxy_stream("chat", request.get_json(silent=True) or {})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
