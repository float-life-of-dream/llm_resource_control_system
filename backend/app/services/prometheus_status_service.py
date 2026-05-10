from __future__ import annotations

from datetime import UTC, datetime

from app.services.model_monitor_service import OVERVIEW_CONFIG as MODEL_OVERVIEW_CONFIG
from app.services.monitor_service import METRIC_CONFIG


class PrometheusStatusService:
    def __init__(self, prometheus_client):
        self.prometheus_client = prometheus_client

    def get_health(self):
        self.prometheus_client.health()
        return {
            "status": "up",
            "baseUrl": self.prometheus_client.base_url,
            "generatedAt": datetime.now(UTC),
        }

    def get_targets(self):
        data = self.prometheus_client.targets()
        active_targets = data.get("activeTargets", [])
        items = []
        for target in active_targets:
            labels = target.get("labels", {})
            discovered = target.get("discoveredLabels", {})
            items.append(
                {
                    "job": str(labels.get("job") or discovered.get("__meta_kubernetes_service_name") or ""),
                    "instance": str(labels.get("instance") or target.get("scrapeUrl") or ""),
                    "health": str(target.get("health") or "unknown"),
                    "scrapeUrl": str(target.get("scrapeUrl") or ""),
                    "lastScrape": self._parse_timestamp(target.get("lastScrape")),
                    "lastError": str(target.get("lastError") or ""),
                }
            )

        return {
            "generatedAt": datetime.now(UTC),
            "items": sorted(items, key=lambda item: (item["job"], item["instance"])),
        }

    def get_metrics(self):
        host_items = []
        gpu_items = []
        for key, config in METRIC_CONFIG.items():
            item = {"key": key, "label": config["label"], "unit": config["unit"]}
            if key.startswith("gpu"):
                gpu_items.append(item)
            else:
                host_items.append(item)

        model_items = [
            {"key": key, "label": config["label"], "unit": config["unit"]}
            for key, config in MODEL_OVERVIEW_CONFIG.items()
        ]

        return {
            "generatedAt": datetime.now(UTC),
            "groups": [
                {"key": "host", "label": "Host Metrics", "items": host_items},
                {"key": "gpu", "label": "GPU Metrics", "items": gpu_items},
                {"key": "model", "label": "Ollama Model Metrics", "items": model_items},
            ],
        }

    @staticmethod
    def _parse_timestamp(value: str | None):
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
