from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship

from app.extensions.db import db


def utcnow() -> datetime:
    return datetime.now(UTC)


class TenantRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    VIEWER = "viewer"


class Tenant(db.Model):
    __tablename__ = "tenants"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(64), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    memberships = relationship("TenantMembership", back_populates="tenant", cascade="all, delete-orphan")
    refresh_sessions = relationship("RefreshTokenSession", back_populates="tenant")
    analysis_sessions = relationship("AnalysisSession", back_populates="tenant", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="tenant", cascade="all, delete-orphan")


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    full_name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_system_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    memberships = relationship("TenantMembership", back_populates="user", cascade="all, delete-orphan")
    refresh_sessions = relationship("RefreshTokenSession", back_populates="user", cascade="all, delete-orphan")
    analysis_sessions = relationship("AnalysisSession", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")


class TenantMembership(db.Model):
    __tablename__ = "tenant_memberships"
    __table_args__ = (UniqueConstraint("tenant_id", "user_id", name="uq_tenant_membership_tenant_user"),)

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    role = db.Column(db.Enum(TenantRole), nullable=False, default=TenantRole.VIEWER)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    tenant = relationship("Tenant", back_populates="memberships")
    user = relationship("User", back_populates="memberships")


class RefreshTokenSession(db.Model):
    __tablename__ = "refresh_token_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    refresh_jti = db.Column(db.String(36), nullable=False, unique=True, index=True)
    user_agent = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    last_used_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    user = relationship("User", back_populates="refresh_sessions")
    tenant = relationship("Tenant", back_populates="refresh_sessions")


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisSession(db.Model):
    __tablename__ = "analysis_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    range_value = db.Column(db.String(8), nullable=False)
    log_query = db.Column(db.String(255), nullable=True)
    log_limit = db.Column(db.Integer, nullable=False)
    include_metrics = db.Column(db.Boolean, nullable=False, default=True)
    status = db.Column(db.Enum(AnalysisStatus), nullable=False, default=AnalysisStatus.PENDING)
    model_name = db.Column(db.String(128), nullable=False)
    duration_ms = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    tenant = relationship("Tenant", back_populates="analysis_sessions")
    user = relationship("User", back_populates="analysis_sessions")
    result = relationship("AnalysisResult", back_populates="session", uselist=False, cascade="all, delete-orphan")
    evidence = relationship("AnalysisEvidence", back_populates="session", uselist=False, cascade="all, delete-orphan")


class AnalysisResult(db.Model):
    __tablename__ = "analysis_results"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_session_id = db.Column(db.String(36), db.ForeignKey("analysis_sessions.id"), nullable=False, unique=True, index=True)
    summary = db.Column(db.Text, nullable=True)
    anomalies = db.Column(db.JSON, nullable=False, default=list)
    recommendations = db.Column(db.JSON, nullable=False, default=list)
    raw_model_output = db.Column(db.Text, nullable=True)
    risk_metadata = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    session = relationship("AnalysisSession", back_populates="result")


class AnalysisEvidence(db.Model):
    __tablename__ = "analysis_evidence"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_session_id = db.Column(db.String(36), db.ForeignKey("analysis_sessions.id"), nullable=False, unique=True, index=True)
    metrics_snapshot = db.Column(db.JSON, nullable=False, default=dict)
    log_excerpt = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    session = relationship("AnalysisSession", back_populates="evidence")


class ChatRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(160), nullable=False)
    model = db.Column(db.String(128), nullable=False)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    tenant = relationship("Tenant", back_populates="chat_sessions")
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = db.Column(db.Enum(ChatRole), nullable=False)
    content = db.Column(db.Text, nullable=False)
    raw_metadata = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    session = relationship("ChatSession", back_populates="messages")

