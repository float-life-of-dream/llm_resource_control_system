from __future__ import annotations

from datetime import UTC, datetime, timedelta


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
    "gpu_memory_used": {
        "label": "GPU Memory",
        "unit": "MiB",
        "overview_query": "sum(DCGM_FI_DEV_FB_USED)",
        "timeseries_query": "sum(DCGM_FI_DEV_FB_USED)",
    },
    "gpu_memory_utilization": {
        "label": "GPU Memory %",
        "unit": "%",
        "overview_query": "100 * sum(DCGM_FI_DEV_FB_USED) / clamp_min(sum(DCGM_FI_DEV_FB_TOTAL), 1)",
        "timeseries_query": "100 * sum(DCGM_FI_DEV_FB_USED) / clamp_min(sum(DCGM_FI_DEV_FB_TOTAL), 1)",
    },
    "gpu_utilization": {
        "label": "GPU Utilization",
        "unit": "%",
        "overview_query": "avg(DCGM_FI_DEV_GPU_UTIL)",
        "timeseries_query": "avg(DCGM_FI_DEV_GPU_UTIL)",
    },
    "gpu_temperature": {
        "label": "GPU Temperature",
        "unit": "C",
        "overview_query": "avg(DCGM_FI_DEV_GPU_TEMP)",
        "timeseries_query": "avg(DCGM_FI_DEV_GPU_TEMP)",
    },
    "gpu_power_usage": {
        "label": "GPU Power",
        "unit": "W",
        "overview_query": "avg(DCGM_FI_DEV_POWER_USAGE)",
        "timeseries_query": "avg(DCGM_FI_DEV_POWER_USAGE)",
    },
}

GPU_DEVICE_QUERIES = {
    "memoryUsedMiB": "DCGM_FI_DEV_FB_USED",
    "memoryTotalMiB": "DCGM_FI_DEV_FB_TOTAL",
    "utilizationPercent": "DCGM_FI_DEV_GPU_UTIL",
    "memoryUtilizationPercent": "100 * DCGM_FI_DEV_FB_USED / clamp_min(DCGM_FI_DEV_FB_TOTAL, 1)",
    "temperatureCelsius": "DCGM_FI_DEV_GPU_TEMP",
    "powerUsageWatts": "DCGM_FI_DEV_POWER_USAGE",
}

RANGE_TO_DELTA = {"1h": timedelta(hours=1), "6h": timedelta(hours=6), "24h": timedelta(hours=24)}


class MonitorService:
    def __init__(self, prometheus_client):
        self.prometheus_client = prometheus_client

    def get_overview(self):
        items = []
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

    def get_timeseries(self, metric: str, range_value: str, step: str):
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
        points = []
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

    def get_gpu_devices(self):
        devices: dict[str, dict] = {}
        for field, query in GPU_DEVICE_QUERIES.items():
            data = self.prometheus_client.query(query)
            for result in data.get("result", []):
                labels = result.get("metric", {})
                device_id = self._gpu_device_id(labels)
                if device_id not in devices:
                    devices[device_id] = self._empty_gpu_device(device_id, labels)
                devices[device_id][field] = round(float(result.get("value", [0, 0])[1]), 2)

        for device in devices.values():
            used = device["memoryUsedMiB"]
            total = device["memoryTotalMiB"]
            if total > 0 and device["memoryUtilizationPercent"] == 0:
                device["memoryUtilizationPercent"] = round(used / total * 100, 2)
            device["status"] = "active" if any(
                device[key] > 0
                for key in [
                    "memoryUsedMiB",
                    "memoryTotalMiB",
                    "utilizationPercent",
                    "temperatureCelsius",
                    "powerUsageWatts",
                ]
            ) else "unknown"

        return {
            "generatedAt": datetime.now(UTC),
            "items": sorted(devices.values(), key=lambda item: item["id"]),
        }

    @staticmethod
    def _gpu_device_id(labels: dict) -> str:
        return (
            labels.get("UUID")
            or labels.get("uuid")
            or labels.get("gpu")
            or labels.get("device")
            or labels.get("minor_number")
            or labels.get("instance")
            or "gpu-unknown"
        )

    @staticmethod
    def _empty_gpu_device(device_id: str, labels: dict) -> dict:
        return {
            "id": str(device_id),
            "name": str(labels.get("modelName") or labels.get("model_name") or labels.get("name") or labels.get("gpu") or device_id),
            "uuid": str(labels.get("UUID") or labels.get("uuid") or ""),
            "memoryUsedMiB": 0.0,
            "memoryTotalMiB": 0.0,
            "memoryUtilizationPercent": 0.0,
            "utilizationPercent": 0.0,
            "temperatureCelsius": 0.0,
            "powerUsageWatts": 0.0,
            "status": "unknown",
        }
