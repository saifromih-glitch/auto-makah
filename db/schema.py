"""
Auto Makah — PostgreSQL Database Schema
SQLAlchemy async with UUID PKs, indexes, FK constraints, and relationships.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Mixin — auto timestamps
# ---------------------------------------------------------------------------

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# 1. tenants
# ---------------------------------------------------------------------------

class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    plan: Mapped[str] = mapped_column(
        String(20), nullable=False, default="free", server_default="free"
    )
    api_key: Mapped[str | None] = mapped_column(String(128), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    settings: Mapped[dict | None] = mapped_column(JSONB)

    # relationships
    users: Mapped[list["User"]] = relationship(back_populates="tenant", lazy="selectin")
    agents: Mapped[list["Agent"]] = relationship(back_populates="tenant", lazy="selectin")
    knowledge_entries: Mapped[list["KnowledgeEntry"]] = relationship(back_populates="tenant", lazy="selectin")
    experts: Mapped[list["Expert"]] = relationship(back_populates="tenant", lazy="selectin")

    __table_args__ = (
        Index("ix_tenants_email", "email"),
        Index("ix_tenants_api_key", "api_key"),
        Index("ix_tenants_plan", "plan"),
        Index("ix_tenants_is_active", "is_active"),
    )


# ---------------------------------------------------------------------------
# 2. users
# ---------------------------------------------------------------------------

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="user", server_default="user"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    # relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="users")
    sessions: Mapped[list["Session"]] = relationship(back_populates="user", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        Index("ix_users_role", "role"),
        Index("ix_users_is_active", "is_active"),
    )


# ---------------------------------------------------------------------------
# 3. agents
# ---------------------------------------------------------------------------

class Agent(Base, TimestampMixin):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    profile: Mapped[dict | None] = mapped_column(JSONB)
    system_prompt: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    tools_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    # relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="agents")
    tools: Mapped[list["Tool"]] = relationship(back_populates="agent", lazy="selectin")
    sessions: Mapped[list["Session"]] = relationship(back_populates="agent", lazy="selectin")
    channels: Mapped[list["Channel"]] = relationship(back_populates="agent", lazy="selectin")

    __table_args__ = (
        Index("ix_agents_name", "tenant_id", "name"),
        Index("ix_agents_is_active", "is_active"),
    )


# ---------------------------------------------------------------------------
# 4. tools
# ---------------------------------------------------------------------------

class Tool(Base, TimestampMixin):
    __tablename__ = "tools"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100))
    parameters: Mapped[dict | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    # relationships
    agent: Mapped["Agent"] = relationship(back_populates="tools")

    __table_args__ = (
        Index("ix_tools_agent_name", "agent_id", "name"),
        Index("ix_tools_category", "category"),
        Index("ix_tools_is_active", "is_active"),
    )


# ---------------------------------------------------------------------------
# 5. knowledge_entries
# ---------------------------------------------------------------------------

class KnowledgeEntry(Base, TimestampMixin):
    __tablename__ = "knowledge_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    domain: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list | None] = mapped_column(JSONB)
    source_url: Mapped[str | None] = mapped_column(String(2048))

    # relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="knowledge_entries")

    __table_args__ = (
        Index("ix_knowledge_tenant_domain", "tenant_id", "domain"),
        Index("ix_knowledge_tags", "tags", postgresql_using="gin"),
    )


# ---------------------------------------------------------------------------
# 6. sessions
# ---------------------------------------------------------------------------

class Session(Base, TimestampMixin):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(500))
    memory: Mapped[dict | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    # relationships
    agent: Mapped["Agent"] = relationship(back_populates="sessions")
    user: Mapped["User"] = relationship(back_populates="sessions")
    messages: Mapped[list["Message"]] = relationship(back_populates="session", lazy="selectin")

    __table_args__ = (
        Index("ix_sessions_agent_user", "agent_id", "user_id"),
        Index("ix_sessions_is_active", "is_active"),
    )


# ---------------------------------------------------------------------------
# 7. messages
# ---------------------------------------------------------------------------

class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # user / agent / system / tool
    content: Mapped[str | None] = mapped_column(Text)
    msg_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB)  # "metadata" clashes with Base.metadata

    # relationships
    session: Mapped["Session"] = relationship(back_populates="messages")

    __table_args__ = (
        Index("ix_messages_session_role", "session_id", "role"),
        Index("ix_messages_created_at", "created_at"),
    )


# ---------------------------------------------------------------------------
# 8. channels
# ---------------------------------------------------------------------------

class Channel(Base, TimestampMixin):
    __tablename__ = "channels"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # telegram / whatsapp
    config: Mapped[dict | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    # relationships
    agent: Mapped["Agent"] = relationship(back_populates="channels")

    __table_args__ = (
        Index("ix_channels_agent_type", "agent_id", "type"),
        Index("ix_channels_is_active", "is_active"),
    )


# ---------------------------------------------------------------------------
# 9. experts
# ---------------------------------------------------------------------------

class Expert(Base, TimestampMixin):
    __tablename__ = "experts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255))
    system_prompt: Mapped[str | None] = mapped_column(Text)
    profile: Mapped[dict | None] = mapped_column(JSONB)
    tools: Mapped[list | None] = mapped_column(JSONB)

    # relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="experts")

    __table_args__ = (
        Index("ix_experts_tenant_domain", "tenant_id", "domain"),
        Index("ix_experts_name", "name"),
    )
