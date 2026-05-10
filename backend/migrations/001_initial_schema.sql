CREATE TABLE tenants (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    slug VARCHAR(64) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_system_admin BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE tenant_memberships (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    role VARCHAR(32) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_tenant_membership_tenant_user UNIQUE (tenant_id, user_id)
);

CREATE TABLE refresh_token_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    refresh_jti VARCHAR(36) NOT NULL UNIQUE,
    user_agent VARCHAR(255),
    ip_address VARCHAR(64),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    last_used_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE analysis_sessions (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    range_value VARCHAR(8) NOT NULL,
    log_query VARCHAR(255),
    log_limit INTEGER NOT NULL,
    include_metrics BOOLEAN NOT NULL DEFAULT TRUE,
    status VARCHAR(32) NOT NULL,
    model_name VARCHAR(128) NOT NULL,
    duration_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ
);

CREATE TABLE analysis_results (
    id VARCHAR(36) PRIMARY KEY,
    analysis_session_id VARCHAR(36) NOT NULL UNIQUE REFERENCES analysis_sessions(id),
    summary TEXT,
    anomalies JSON NOT NULL,
    recommendations JSON NOT NULL,
    raw_model_output TEXT,
    risk_metadata JSON,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE analysis_evidence (
    id VARCHAR(36) PRIMARY KEY,
    analysis_session_id VARCHAR(36) NOT NULL UNIQUE REFERENCES analysis_sessions(id),
    metrics_snapshot JSON NOT NULL,
    log_excerpt JSON NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE chat_sessions (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    title VARCHAR(160) NOT NULL,
    model VARCHAR(128) NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE chat_messages (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL REFERENCES chat_sessions(id),
    role VARCHAR(32) NOT NULL,
    content TEXT NOT NULL,
    raw_metadata JSON NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
