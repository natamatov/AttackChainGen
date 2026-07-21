"""
SQLAlchemy ORM модели для AttackChainGen.

Модели:
  - User         — пользователи системы (admin / instructor)
  - Stand        — подключения к Elasticsearch стендам
  - Playbook     — сценарии атак
  - SimulationRun — история запусков симуляций
  - AuditLog     — аудит действий (опционально)
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


# ─────────────────────────────────────────────────────────────────────── #
# Enums                                                                    #
# ─────────────────────────────────────────────────────────────────────── #

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    INSTRUCTOR = "instructor"


class SimulationStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SimulationMode(str, enum.Enum):
    REALTIME = "realtime"
    HISTORICAL = "historical"


class NoiseLevel(str, enum.Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ─────────────────────────────────────────────────────────────────────── #
# User                                                                     #
# ─────────────────────────────────────────────────────────────────────── #

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.INSTRUCTOR, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    stands: Mapped[list["Stand"]] = relationship(back_populates="created_by_user")
    playbooks: Mapped[list["Playbook"]] = relationship(back_populates="created_by_user")
    simulation_runs: Mapped[list["SimulationRun"]] = relationship(back_populates="created_by_user")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"


# ─────────────────────────────────────────────────────────────────────── #
# Stand                                                                    #
# ─────────────────────────────────────────────────────────────────────── #

class Stand(Base):
    """Стенд — настройки подключения к Elasticsearch."""

    __tablename__ = "stands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    elastic_url: Mapped[str] = mapped_column(String(512), nullable=False)
    api_key: Mapped[str | None] = mapped_column(String(512))
    username: Mapped[str | None] = mapped_column(String(255))
    password: Mapped[str | None] = mapped_column(String(512))
    tenant_id: Mapped[str | None] = mapped_column(String(255))
    index_pattern: Mapped[str] = mapped_column(
        String(255), default="logs-attackchain-default", nullable=False
    )
    verify_ssl: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    created_by_user: Mapped["User | None"] = relationship(back_populates="stands")
    simulation_runs: Mapped[list["SimulationRun"]] = relationship(back_populates="stand")

    def __repr__(self) -> str:
        return f"<Stand id={self.id} name={self.name}>"


# ─────────────────────────────────────────────────────────────────────── #
# Playbook                                                                 #
# ─────────────────────────────────────────────────────────────────────── #

class Playbook(Base):
    """Сценарий атаки (YAML)."""

    __tablename__ = "playbooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    mitre_tactics: Mapped[list | None] = mapped_column(JSON, default=list)
    mitre_techniques: Mapped[list | None] = mapped_column(JSON, default=list)
    yaml_content: Mapped[str] = mapped_column(Text, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    created_by_user: Mapped["User | None"] = relationship(back_populates="playbooks")
    simulation_runs: Mapped[list["SimulationRun"]] = relationship(back_populates="playbook")

    def __repr__(self) -> str:
        return f"<Playbook id={self.id} name={self.name}>"


# ─────────────────────────────────────────────────────────────────────── #
# SimulationRun                                                            #
# ─────────────────────────────────────────────────────────────────────── #

class SimulationRun(Base):
    """Один запуск симуляции."""

    __tablename__ = "simulation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    playbook_id: Mapped[int | None] = mapped_column(ForeignKey("playbooks.id", ondelete="SET NULL"))
    stand_id: Mapped[int | None] = mapped_column(ForeignKey("stands.id", ondelete="SET NULL"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    # Статус
    status: Mapped[SimulationStatus] = mapped_column(
        Enum(SimulationStatus), default=SimulationStatus.PENDING, nullable=False, index=True
    )

    # Конфигурация запуска
    mode: Mapped[SimulationMode] = mapped_column(
        Enum(SimulationMode), default=SimulationMode.REALTIME, nullable=False
    )
    noise_level: Mapped[NoiseLevel] = mapped_column(
        Enum(NoiseLevel), default=NoiseLevel.NONE, nullable=False
    )
    backdate_offset: Mapped[str | None] = mapped_column(String(64))
    overrides: Mapped[dict | None] = mapped_column(JSON, default=dict)

    # Прогресс
    celery_task_id: Mapped[str | None] = mapped_column(String(255))
    progress_current: Mapped[int] = mapped_column(Integer, default=0)
    progress_total: Mapped[int] = mapped_column(Integer, default=0)
    progress_message: Mapped[str | None] = mapped_column(String(512))

    # Результаты
    artifacts: Mapped[dict | None] = mapped_column(JSON, default=dict)
    events_sent: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)

    # Временные метки
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Снапшот имён (чтобы история не рвалась при удалении)
    playbook_name: Mapped[str | None] = mapped_column(String(255))
    stand_name: Mapped[str | None] = mapped_column(String(255))

    # Relationships
    playbook: Mapped["Playbook | None"] = relationship(back_populates="simulation_runs")
    stand: Mapped["Stand | None"] = relationship(back_populates="simulation_runs")
    created_by_user: Mapped["User | None"] = relationship(back_populates="simulation_runs")

    def __repr__(self) -> str:
        return f"<SimulationRun id={self.id} status={self.status}>"


# ─────────────────────────────────────────────────────────────────────── #
# Fictional Network Models (CMDB)                                          #
# ─────────────────────────────────────────────────────────────────────── #

class FictionalEnvironment(Base):
    """Среда / вымышленная сеть (например, corp.local)."""
    __tablename__ = "fictional_environments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    zones: Mapped[list["NetworkZone"]] = relationship(
        back_populates="environment", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<FictionalEnvironment id={self.id} name={self.name}>"


class NetworkZone(Base):
    """Сетевая зона (например, Servers 192.168.100.0/24)."""
    __tablename__ = "network_zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    environment_id: Mapped[int] = mapped_column(
        ForeignKey("fictional_environments.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_range: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Relationships
    environment: Mapped["FictionalEnvironment"] = relationship(back_populates="zones")
    assets: Mapped[list["Asset"]] = relationship(
        back_populates="zone", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<NetworkZone id={self.id} name={self.name} ip_range={self.ip_range}>"


class Asset(Base):
    """Конкретный узел сети (сервер, рабочая станция)."""
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    zone_id: Mapped[int] = mapped_column(
        ForeignKey("network_zones.id", ondelete="CASCADE"), nullable=False
    )
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str | None] = mapped_column(String(255))

    # Relationships
    zone: Mapped["NetworkZone"] = relationship(back_populates="assets")

    def __repr__(self) -> str:
        return f"<Asset id={self.id} hostname={self.hostname} ip={self.ip_address}>"
