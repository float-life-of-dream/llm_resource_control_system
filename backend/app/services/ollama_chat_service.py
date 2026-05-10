from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterator

import requests


class OllamaChatError(RuntimeError):
    pass


@dataclass
class OllamaChatService:
    base_url: str
    timeout: float = 30.0

    def stream_chat(self, *, model: str, messages: list[dict]) -> Iterator[dict]:
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        try:
            response = requests.post(
                f"{self.base_url.rstrip('/')}/api/chat",
                json=payload,
                stream=True,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            raise OllamaChatError("Ollama chat request timed out") from exc
        except requests.RequestException as exc:
            raise OllamaChatError("Ollama chat request failed") from exc

        try:
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    yield json.loads(line.decode("utf-8"))
                except json.JSONDecodeError as exc:
                    raise OllamaChatError("Ollama returned an invalid stream payload") from exc
        finally:
            response.close()
