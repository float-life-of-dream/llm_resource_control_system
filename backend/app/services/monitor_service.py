from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any


METRIC_CONFIG = {
    "cpu": {
        "label": "CPU",
        "unit": "%",
        "overview_query": 'avg(100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100))',
        "timeseries_query": '100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
    },
    "memory": {
        "label": "Memory",
        "unit": "GiB",
        "overview_query": "(sum(node_memory_MemTotal_bytes) - sum(node_memory_MemAvailable_bytes)) / 1024 / 1024 / 1024",
        "timeseries_query": "(sum(node_memory_MemTotal_bytes) - sum(node_memory_MemAvailable_bytes)) / 1024 / 1024 / 1024",
    },
    "disk": {
        "label": "Disk",
        "unit": "%",
        "overview_query": "100 * (1 - (sum(node_filesystem_avail_bytes{fstype!=\"tmpfs\"}) / sum(node_filesystem_size_bytes{fstype!=\"tmpfs\"})))",
        "timeseries_query": "100 * (1 - (sum(node_filesystem_avail_bytes{fstype!=\"tmpfs\"}) / sum(node_filesystem_size_bytes{fstype!=\"tmpfs\"})))",
    },
    "gpu": {
        "label": "GPU",
        "unit": "MiB",
        "overview_query": "sum(DCGM_FI_DEV_FB_USED)",
        "timeseries_query": "sum(DCGM_FI_DEV_FB_USED)",
    },
}

RANGE_TO_DELTA = {"1h": timedelta(hours=1), "6h": timedelta(hours=6), "24h": timedelta(hours=24)}


class MonitorService:
    def __init__(self, prometheus_client: Any) -> None:
        self.prometheus_client = prometheus_client

    def get_overview(self) -> dict[str, Any]:
        items: list[dict[str, Any]] = []
        for metric, config in METRIC_CONFIG.items():
            data = self.prometheus_client.query(config["overview_query"])
            result = data.get("result", [])
            value = 0.0
            if result:
                value = float(result[0]["value"][1])
            items.append(
                {
                    "metric": metric,
                    "label": config["label"],
                    "value": round(value, 2),
                    "unit": config["unit"],
                }
            )

        return {"generatedAt": datetime.now(UTC), "items": items}

    def get_timeseries(self, metric: str, range_value: str, step: str) -> dict[str, Any]:
        config = METRIC_CONFIG[metric]
        now = datetime.now(UTC)
        start = now - RANGE_TO_DELTA[range_value]
        data = self.prometheus_client.query_range(
            config["timeseries_query"],
            start.isoformat(),
            now.isoformat(),
            step,
        )
        result = data.get("result", [])
        points: list[dict[str, Any]] = []
        if result:
            for timestamp, value in result[0].get("values", []):
                points.append(
                    {
                        "timestamp": datetime.fromtimestamp(float(timestamp), UTC),
                        "value": round(float(value), 2),
                        "unit": config["unit"],
                    }
                )

        return {
            "metric": metric,
            "range": range_value,
            "step": step,
            "series": points,
        }
