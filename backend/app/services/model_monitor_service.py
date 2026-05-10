from __future__ import annotations

from datetime import UTC, datetime, timedelta


RANGE_TO_DELTA = {"1h": timedelta(hours=1), "6h": timedelta(hours=6), "24h": timedelta(hours=24)}

OVERVIEW_CONFIG = {
    "request_rate": {
        "label": "Request Rate",
        "unit": "req/s",
        "query": "sum(rate(ollama_requests_total[5m]))",
    },
    "latency": {
        "label": "Avg Latency",
        "unit": "s",
        "query": "sum(rate(ollama_request_duration_seconds_sum[5m])) / clamp_min(sum(rate(ollama_request_duration_seconds_count[5m])), 1)",
    },
    "concurrency": {
        "label": "Active Requests",
        "unit": "",
        "query": "sum(ollama_active_requests)",
    },
    "loaded_models": {
        "label": "Loaded Models",
        "unit": "",
        "query": "sum(ollama_loaded_models)",
    },
    "tokens_per_second": {
        "label": "Tokens/sec",
        "unit": "tok/s",
        "query": "sum(ollama_tokens_per_second)",
    },
    "error_rate": {
        "label": "Error Rate",
        "unit": "err/s",
        "query": 'sum(rate(ollama_requests_total{status="error"}[5m]))',
    },
}

TIMESERIES_CONFIG = {
    "request_rate": {
        "unit": "req/s",
        "query": "sum(rate(ollama_requests_total[5m]))",
    },
    "latency": {
        "unit": "s",
        "query": "sum(rate(ollama_request_duration_seconds_sum[5m])) / clamp_min(sum(rate(ollama_request_duration_seconds_count[5m])), 1)",
    },
    "concurrency": {
        "unit": "",
        "query": "sum(ollama_active_requests)",
    },
    "tokens_per_second": {
        "unit": "tok/s",
        "query": "sum(ollama_tokens_per_second)",
    },
    "error_rate": {
        "unit": "err/s",
        "query": 'sum(rate(ollama_requests_total{status="error"}[5m]))',
    },
    "loaded_models": {
        "unit": "",
        "query": "sum(ollama_loaded_models)",
    },
}


class ModelMonitorService:
    def __init__(self, prometheus_client):
        self.prometheus_client = prometheus_client

    def get_overview(self):
        items = []
        for metric, config in OVERVIEW_CONFIG.items():
            items.append(
                {
                    "metric": metric,
                    "label": config["label"],
                    "value": self._query_scalar(config["query"]),
                    "unit": config["unit"],
                }
            )
        return {"generatedAt": datetime.now(UTC), "items": items}

    def get_models(self):
        now = datetime.now(UTC)
        memory_by_model = self._query_vector("ollama_model_memory_bytes")
        context_by_model = self._query_vector("ollama_model_context_window")
        info_by_model = self._query_info("ollama_model_quantization_info")

        model_names = sorted(set(memory_by_model) | set(context_by_model) | set(info_by_model))
        items = []
        for name in model_names:
            info = info_by_model.get(name, {})
            items.append(
                {
                    "name": name,
                    "parameterSize": info.get("parameter_size"),
                    "quantization": info.get("quantization"),
                    "contextWindow": int(context_by_model[name]) if name in context_by_model else None,
                    "memoryBytes": int(memory_by_model.get(name, 0)),
                    "status": "loaded",
                    "lastSeenAt": now,
                }
            )

        return {"generatedAt": now, "items": items}

    def get_timeseries(self, metric: str, range_value: str, step: str):
        config = TIMESERIES_CONFIG[metric]
        now = datetime.now(UTC)
        start = now - RANGE_TO_DELTA[range_value]
        data = self.prometheus_client.query_range(
            config["query"],
            start.isoformat(),
            now.isoformat(),
            step,
        )
        result = data.get("result", [])
        points = []
        if result:
            for timestamp, value in result[0].get("values", []):
                points.append(
                    {
                        "timestamp": datetime.fromtimestamp(float(timestamp), UTC),
                        "value": round(float(value), 4),
                        "unit": config["unit"],
                    }
                )

        return {"metric": metric, "range": range_value, "step": step, "series": points}

    def _query_scalar(self, promql: str) -> float:
        data = self.prometheus_client.query(promql)
        result = data.get("result", [])
        if not result:
            return 0.0
        return round(float(result[0]["value"][1]), 4)

    def _query_vector(self, promql: str) -> dict[str, float]:
        data = self.prometheus_client.query(promql)
        values = {}
        for item in data.get("result", []):
            model = item.get("metric", {}).get("model")
            if model:
                values[model] = float(item["value"][1])
        return values

    def _query_info(self, promql: str) -> dict[str, dict[str, str]]:
        data = self.prometheus_client.query(promql)
        values = {}
        for item in data.get("result", []):
            labels = item.get("metric", {})
            model = labels.get("model")
            if model:
                values[model] = {
                    "parameter_size": labels.get("parameter_size"),
                    "quantization": labels.get("quantization"),
                }
        return values
