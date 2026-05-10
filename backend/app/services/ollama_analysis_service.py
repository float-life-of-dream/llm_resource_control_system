from __future__ import annotations

import json
from dataclasses import dataclass
from time import perf_counter

import requests

from app.extensions.metrics import OLLAMA_REQUEST_DURATION_SECONDS


class OllamaAnalysisError(RuntimeError):
    def __init__(self, message: str, raw_output: str = ""):
        super().__init__(message)
        self.raw_output = raw_output


@dataclass
class OllamaAnalysisService:
    base_url: str
    model: str
    timeout: float = 30.0

    def analyze(self, *, range_value: str, metrics_snapshot: dict, logs: list[dict]) -> dict:
        prompt = self._build_prompt(range_value=range_value, metrics_snapshot=metrics_snapshot, logs=logs)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }
        started_at = perf_counter()
        try:
            response = requests.post(
                f"{self.base_url.rstrip('/')}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            OLLAMA_REQUEST_DURATION_SECONDS.observe(perf_counter() - started_at)
            raise OllamaAnalysisError("Ollama request timed out") from exc
        except requests.RequestException as exc:
            OLLAMA_REQUEST_DURATION_SECONDS.observe(perf_counter() - started_at)
            raise OllamaAnalysisError("Ollama request failed") from exc
        OLLAMA_REQUEST_DURATION_SECONDS.observe(perf_counter() - started_at)

        body = response.json()
        raw_output = str(body.get("response", "")).strip()
        return self._parse_response(raw_output)

    @staticmethod
    def _build_prompt(*, range_value: str, metrics_snapshot: dict, logs: list[dict]) -> str:
        return (
            "You are an operations analysis assistant. "
            "Analyze the provided metrics snapshot and logs. "
            "Return strict JSON with keys: summary, anomalies, recommendations. "
            "summary must be a concise string. anomalies and recommendations must be arrays of short strings. "
            "Do not output markdown.\n\n"
            f"Time range: {range_value}\n"
            f"Metrics snapshot: {json.dumps(metrics_snapshot, ensure_ascii=True)}\n"
            f"Logs: {json.dumps(logs, ensure_ascii=True)}"
        )

    @staticmethod
    def _parse_response(raw_output: str) -> dict:
        try:
            parsed = json.loads(raw_output)
        except json.JSONDecodeError:
            start = raw_output.find("{")
            end = raw_output.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise OllamaAnalysisError("Ollama returned an invalid JSON payload", raw_output)
            try:
                parsed = json.loads(raw_output[start : end + 1])
            except json.JSONDecodeError as exc:
                raise OllamaAnalysisError("Ollama returned an invalid JSON payload", raw_output) from exc

        summary = parsed.get("summary")
        anomalies = parsed.get("anomalies")
        recommendations = parsed.get("recommendations")
        if not isinstance(summary, str) or not isinstance(anomalies, list) or not isinstance(recommendations, list):
            raise OllamaAnalysisError("Ollama returned an unexpected analysis structure", raw_output)

        return {
            "summary": summary.strip(),
            "anomalies": [str(item).strip() for item in anomalies if str(item).strip()],
            "recommendations": [str(item).strip() for item in recommendations if str(item).strip()],
            "rawOutput": raw_output,
        }
