from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import requests


class ElasticsearchLogError(RuntimeError):
    pass


def _level_rank(level: str) -> int:
    normalized = level.lower()
    if normalized == "error":
        return 0
    if normalized == "warning" or normalized == "warn":
        return 1
    return 2


@dataclass
class ElasticsearchLogService:
    base_url: str
    index: str
    username: str = ""
    password: str = ""
    timeout: float = 10.0

    def search_logs(self, tenant_id: str, range_value: str, log_query: str, limit: int) -> list[dict]:
        now = datetime.now(UTC)
        start = now - self._range_delta(range_value)
        payload = {
            "size": min(limit * 3, 500),
            "sort": [{"@timestamp": {"order": "desc"}}],
            "query": {
                "bool": {
                    "filter": [
                        {"range": {"@timestamp": {"gte": start.isoformat(), "lte": now.isoformat()}}},
                        {
                            "bool": {
                                "should": [
                                    {"term": {"tenant_id.keyword": tenant_id}},
                                    {"term": {"tenant_id": tenant_id}},
                                    {"term": {"tenant.id.keyword": tenant_id}},
                                    {"term": {"tenant.id": tenant_id}},
                                ],
                                "minimum_should_match": 1,
                            }
                        },
                    ]
                }
            },
        }
        if log_query:
            payload["query"]["bool"]["must"] = [
                {
                    "simple_query_string": {
                        "query": log_query,
                        "fields": ["message^3", "log.level", "service.name", "service"],
                        "default_operator": "and",
                    }
                }
            ]

        auth = (self.username, self.password) if self.username else None
        try:
            response = requests.post(
                f"{self.base_url.rstrip('/')}/{self.index}/_search",
                json=payload,
                auth=auth,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            raise ElasticsearchLogError("Elasticsearch request timed out") from exc
        except requests.RequestException as exc:
            raise ElasticsearchLogError("Elasticsearch request failed") from exc

        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        normalized = [self._normalize_hit(hit) for hit in hits]
        deduplicated: list[dict] = []
        seen: set[tuple[str, str, str]] = set()
        for item in normalized:
            key = (item["service"], item["level"], item["message"])
            if key in seen:
                continue
            seen.add(key)
            deduplicated.append(item)

        deduplicated.sort(key=lambda item: (_level_rank(item["level"]), item["timestamp"]), reverse=False)
        return deduplicated[:limit]

    @staticmethod
    def _range_delta(range_value: str) -> timedelta:
        if range_value == "6h":
            return timedelta(hours=6)
        if range_value == "24h":
            return timedelta(hours=24)
        return timedelta(hours=1)

    @staticmethod
    def _normalize_hit(hit: dict) -> dict:
        source = hit.get("_source", {})
        message = (
            source.get("message")
            or source.get("log", {}).get("original")
            or source.get("event", {}).get("original")
            or ""
        )
        service = source.get("service", {}).get("name") or source.get("service") or "unknown"
        level = source.get("log", {}).get("level") or source.get("level") or "info"
        timestamp = source.get("@timestamp") or source.get("timestamp") or ""
        return {
            "timestamp": timestamp,
            "level": str(level),
            "service": str(service),
            "message": str(message)[:1000],
        }
