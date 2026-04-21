from __future__ import annotations

import os


class Config:
    API_TITLE = "AI Monitor API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/api/docs"
    OPENAPI_SWAGGER_UI_PATH = "/"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    JSON_SORT_KEYS = False

    PROMETHEUS_BASE_URL = os.getenv("PROMETHEUS_BASE_URL", "http://prometheus:9090")
    PROMETHEUS_TIMEOUT = float(os.getenv("PROMETHEUS_TIMEOUT", "5"))

    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB = os.getenv("POSTGRES_DB", "ai_monitor")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "ai_monitor")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "ai_monitor")

