from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from math import ceil


CPU_OVERVIEW_QUERY = 'avg(100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100))'
CPU_TIMESERIES_QUERY = '100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
MEMORY_QUERY = "(sum(node_memory_MemTotal_bytes) - sum(node_memory_MemAvailable_bytes)) / 1024 / 1024 / 1024"
DISK_QUERY = '100 * (1 - (sum(node_filesystem_avail_bytes{fstype!="tmpfs"}) / sum(node_filesystem_size_bytes{fstype!="tmpfs"})))'
GPU_QUERY = "sum(DCGM_FI_DEV_FB_USED)"


@dataclass(frozen=True)
class MetricSample:
    metric: str
    query: str
    range_query: str
    unit: str
    overview_value: float
    curve: tuple[float, ...]


METRIC_SAMPLES = {
    "cpu": MetricSample(
        metric="cpu",
        query=CPU_OVERVIEW_QUERY,
        range_query=CPU_TIMESERIES_QUERY,
        unit="%",
        overview_value=42.5,
        curve=(31.2, 34.8, 39.4, 41.1, 43.0, 45.6, 47.9, 46.2, 44.0, 42.5),
    ),
    "memory": MetricSample(
        metric="memory",
        query=MEMORY_QUERY,
        range_query=MEMORY_QUERY,
        unit="GiB",
        overview_value=12.3,
        curve=(11.4, 11.6, 11.8, 12.0, 12.1, 12.2, 12.4, 12.5, 12.4, 12.3),
    ),
    "disk": MetricSample(
        metric="disk",
        query=DISK_QUERY,
        range_query=DISK_QUERY,
        unit="%",
        overview_value=68.4,
        curve=(65.1, 65.9, 66.3, 66.9, 67.2, 67.8, 68.0, 68.2, 68.3, 68.4),
    ),
    "gpu": MetricSample(
        metric="gpu",
        query=GPU_QUERY,
        range_query=GPU_QUERY,
        unit="MiB",
        overview_value=8192.0,
        curve=(6144, 6400, 6656, 6912, 7168, 7424, 7680, 7936, 8064, 8192),
    ),
}

QUERY_INDEX = {}
for sample in METRIC_SAMPLES.values():
    QUERY_INDEX[sample.query] = sample
    QUERY_INDEX[sample.range_query] = sample


def parse_rfc3339(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def parse_step_seconds(value: str) -> int:
    if value.endswith("s"):
        return int(value[:-1])
    if value.endswith("m"):
        return int(value[:-1]) * 60
    if value.endswith("h"):
        return int(value[:-1]) * 3600
    raise ValueError(f"Unsupported step value: {value}")


def build_instant_result(query: str):
    sample = QUERY_INDEX.get(query)
    if sample is None:
        return None

    return {
        "resultType": "vector",
        "result": [
            {
                "metric": {"__name__": f"{sample.metric}_demo"},
                "value": [int(datetime.now(UTC).timestamp()), str(sample.overview_value)],
            }
        ],
    }


def build_range_result(query: str, start: str, end: str, step: str):
    sample = QUERY_INDEX.get(query)
    if sample is None:
        return None

    start_at = parse_rfc3339(start)
    end_at = parse_rfc3339(end)
    step_seconds = parse_step_seconds(step)
    duration_seconds = max(int((end_at - start_at).total_seconds()), 0)
    total_points = max(ceil(duration_seconds / step_seconds) + 1, 2)

    values = []
    for index in range(total_points):
        timestamp = int(start_at.timestamp()) + (index * step_seconds)
        if timestamp > int(end_at.timestamp()):
            timestamp = int(end_at.timestamp())

        curve_index = min(
            round(index * (len(sample.curve) - 1) / max(total_points - 1, 1)),
            len(sample.curve) - 1,
        )
        values.append([timestamp, str(sample.curve[curve_index])])

        if timestamp >= int(end_at.timestamp()):
            break

    return {
        "resultType": "matrix",
        "result": [
            {
                "metric": {"__name__": f"{sample.metric}_demo"},
                "values": values,
            }
        ],
    }
