from __future__ import annotations

import os
from datetime import timedelta


def _build_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    user = os.getenv("POSTGRES_USER", "ai_monitor")
    password = os.getenv("POSTGRES_PASSWORD", "ai_monitor")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "ai_monitor")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"


class Config:
    API_TITLE = "AI Monitor API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/api/docs"
    OPENAPI_SWAGGER_UI_PATH = "/"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    JSON_SORT_KEYS = False
    SQLALCHEMY_DATABASE_URI = _build_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    FRONTEND_ORIGINS = [
        origin.strip()
        for origin in os.getenv("FRONTEND_ORIGIN", "http://localhost:8080,http://localhost:5173").split(",")
        if origin.strip()
    ]
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    JWT_ACCESS_TTL = timedelta(minutes=int(os.getenv("JWT_ACCESS_TTL_MINUTES", "15")))
    JWT_REFRESH_TTL = timedelta(days=int(os.getenv("JWT_REFRESH_TTL_DAYS", "7")))

    PROMETHEUS_BASE_URL = os.getenv("PROMETHEUS_BASE_URL", "http://prometheus:9090")
    PROMETHEUS_TIMEOUT = float(os.getenv("PROMETHEUS_TIMEOUT", "5"))

    BOOTSTRAP_ADMIN_EMAIL = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@example.local")
    BOOTSTRAP_ADMIN_PASSWORD = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "ChangeMe123!")
    BOOTSTRAP_DEFAULT_TENANT_NAME = os.getenv("BOOTSTRAP_DEFAULT_TENANT_NAME", "Default Tenant")
    BOOTSTRAP_DEFAULT_TENANT_SLUG = os.getenv("BOOTSTRAP_DEFAULT_TENANT_SLUG", "default")
