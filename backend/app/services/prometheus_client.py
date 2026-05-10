from __future__ import annotations

from dataclasses import dataclass

import requests


class PrometheusClientError(RuntimeError):
    pass


@dataclass
class PrometheusClient:
    base_url: str
    timeout: float = 5.0

    def query(self, promql: str):
        return self._request("/api/v1/query", {"query": promql})

    def query_range(self, promql: str, start: str, end: str, step: str):
        return self._request(
            "/api/v1/query_range",
            {
                "query": promql,
                "start": start,
                "end": end,
                "step": step,
            },
        )

    def health(self):
        return self._request("/api/v1/status/runtimeinfo")

    def targets(self):
        return self._request("/api/v1/targets")

    def _request(self, path: str, params: dict | None = None):
        try:
            response = requests.get(
                f"{self.base_url.rstrip('/')}{path}",
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            raise PrometheusClientError("Prometheus request timed out") from exc
        except requests.RequestException as exc:
            raise PrometheusClientError("Prometheus request failed") from exc

        payload = response.json()
        if payload.get("status") != "success":
            raise PrometheusClientError(payload.get("error", "Prometheus returned an error"))

        return payload.get("data", {})
