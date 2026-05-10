from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from time import perf_counter

import requests

from app.extensions.metrics import ELASTICSEARCH_QUERY_DURATION_SECONDS


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

    def search_logs(
        self,
        tenant_id: str,
        range_value: str,
        log_query: str,
        limit: int,
        level: str | None = None,
        service: str | None = None,
    ) -> list[dict]:
        payload = self._build_search_payload(
            tenant_id=tenant_id,
            range_value=range_value,
            log_query=log_query,
            size=min(limit * 3, 500),
            level=level,
            service=service,
        )
        data = self._post_search(payload)
        hits = data.get("hits", {}).get("hits", [])
        normalized = [self._normalize_hit(hit) for hit in hits]
        deduplicated = self._dedupe_logs(normalized)
        deduplicated.sort(key=lambda item: (_level_rank(item["level"]), item["timestamp"]), reverse=False)
        return deduplicated[:limit]

    def search_log_page(
        self,
        tenant_id: str,
        range_value: str,
        log_query: str,
        limit: int,
        level: str | None = None,
        service: str | None = None,
    ) -> dict:
        capped_limit = min(max(limit, 1), 500)
        payload = self._build_search_payload(
            tenant_id=tenant_id,
            range_value=range_value,
            log_query=log_query,
            size=capped_limit,
            level=level,
            service=service,
        )
        data = self._post_search(payload)
        hits = data.get("hits", {}).get("hits", [])
        total = data.get("hits", {}).get("total", 0)
        if isinstance(total, dict):
            total_value = int(total.get("value", 0))
        else:
            total_value = int(total or 0)
        return {
            "items": [self._normalize_hit(hit) for hit in hits],
            "total": total_value,
        }

    def get_summary(self, tenant_id: str, range_value: str, log_query: str) -> dict:
        payload = self._build_search_payload(
            tenant_id=tenant_id,
            range_value=range_value,
            log_query=log_query,
            size=0,
        )
        payload["aggs"] = {
            "levels": {"terms": {"field": "log.level.keyword", "size": 10}},
            "levels_fallback": {"terms": {"field": "level.keyword", "size": 10}},
            "services": {"terms": {"field": "service.name.keyword", "size": 50}},
            "services_fallback": {"terms": {"field": "service.keyword", "size": 50}},
        }
        data = self._post_search(payload)
        total = data.get("hits", {}).get("total", 0)
        if isinstance(total, dict):
            total_value = int(total.get("value", 0))
        else:
            total_value = int(total or 0)
        return {
            "total": total_value,
            "levels": self._merge_buckets(
                data.get("aggregations", {}).get("levels", {}),
                data.get("aggregations", {}).get("levels_fallback", {}),
            ),
            "services": self._merge_buckets(
                data.get("aggregations", {}).get("services", {}),
                data.get("aggregations", {}).get("services_fallback", {}),
            ),
        }

    def get_services(self, tenant_id: str, range_value: str) -> list[str]:
        payload = self._build_search_payload(
            tenant_id=tenant_id,
            range_value=range_value,
            log_query="",
            size=0,
        )
        payload["aggs"] = {
            "services": {"terms": {"field": "service.name.keyword", "size": 100}},
            "services_fallback": {"terms": {"field": "service.keyword", "size": 100}},
        }
        data = self._post_search(payload)
        buckets = self._merge_buckets(
            data.get("aggregations", {}).get("services", {}),
            data.get("aggregations", {}).get("services_fallback", {}),
        )
        return [item["key"] for item in buckets if item["key"]]

    def _build_search_payload(
        self,
        tenant_id: str,
        range_value: str,
        log_query: str,
        size: int,
        level: str | None = None,
        service: str | None = None,
    ) -> dict:
        now = datetime.now(UTC)
        start = now - self._range_delta(range_value)
        payload = {
            "size": size,
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
        filters = payload["query"]["bool"]["filter"]
        if level:
            levels = [level]
            if level == "warn":
                levels.append("warning")
            filters.append(
                {
                    "bool": {
                        "should": [
                            term
                            for item in levels
                            for term in (
                                {"term": {"log.level.keyword": item}},
                                {"term": {"level.keyword": item}},
                                {"term": {"log.level": item}},
                                {"term": {"level": item}},
                            )
                        ],
                        "minimum_should_match": 1,
                    }
                }
            )
        if service:
            filters.append(
                {
                    "bool": {
                        "should": [
                            {"term": {"service.name.keyword": service}},
                            {"term": {"service.keyword": service}},
                            {"term": {"service.name": service}},
                            {"term": {"service": service}},
                        ],
                        "minimum_should_match": 1,
                    }
                }
            )
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
        return payload

    def _post_search(self, payload: dict) -> dict:
        auth = (self.username, self.password) if self.username else None
        started_at = perf_counter()
        try:
            response = requests.post(
                f"{self.base_url.rstrip('/')}/{self.index}/_search",
                json=payload,
                auth=auth,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            ELASTICSEARCH_QUERY_DURATION_SECONDS.observe(perf_counter() - started_at)
            raise ElasticsearchLogError("Elasticsearch request timed out") from exc
        except requests.RequestException as exc:
            ELASTICSEARCH_QUERY_DURATION_SECONDS.observe(perf_counter() - started_at)
            raise ElasticsearchLogError("Elasticsearch request failed") from exc
        ELASTICSEARCH_QUERY_DURATION_SECONDS.observe(perf_counter() - started_at)

        return response.json()

    @staticmethod
    def _dedupe_logs(normalized: list[dict]) -> list[dict]:
        deduplicated: list[dict] = []
        seen: set[tuple[str, str, str]] = set()
        for item in normalized:
            key = (item["service"], item["level"], item["message"])
            if key in seen:
                continue
            seen.add(key)
            deduplicated.append(item)
        return deduplicated

    @staticmethod
    def _merge_buckets(*aggregations: dict) -> list[dict]:
        merged: dict[str, int] = {}
        for aggregation in aggregations:
            for bucket in aggregation.get("buckets", []):
                key = str(bucket.get("key", ""))
                if not key:
                    continue
                merged[key] = merged.get(key, 0) + int(bucket.get("doc_count", 0))
        return [
            {"key": key, "count": count}
            for key, count in sorted(merged.items(), key=lambda item: item[1], reverse=True)
        ]

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
        log = source.get("log") if isinstance(source.get("log"), dict) else {}
        event = source.get("event") if isinstance(source.get("event"), dict) else {}
        service_object = source.get("service") if isinstance(source.get("service"), dict) else {}
        host_object = source.get("host") if isinstance(source.get("host"), dict) else {}
        trace_object = source.get("trace") if isinstance(source.get("trace"), dict) else {}
        message = (
            source.get("message")
            or log.get("original")
            or event.get("original")
            or ""
        )
        service = service_object.get("name") or source.get("service") or "unknown"
        level = log.get("level") or source.get("level") or "info"
        timestamp = source.get("@timestamp") or source.get("timestamp") or ""
        return {
            "timestamp": timestamp,
            "level": str(level),
            "service": str(service),
            "message": str(message)[:1000],
            "traceId": trace_object.get("id") or source.get("traceId") or "",
            "host": host_object.get("name") or source.get("host") or "",
            "source": hit.get("_index", ""),
        }
