"""
Playbook Parser — валидация и разбор YAML-сценариев атак.

Pydantic-модели описывают структуру Playbook, шагов и их зависимостей.
Поддерживается разрешение порядка выполнения через топологическую сортировку.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


# ------------------------------------------------------------------ #
# Pydantic Models                                                      #
# ------------------------------------------------------------------ #

class GlobalContext(BaseModel):
    """Глобальные переменные инцидента."""
    host_name: str | None = Field(None, alias="host.name")
    host_domain: str | None = Field(None, alias="host.domain")
    host_ip: str | None = Field(None, alias="host.ip")
    user_name: str | None = Field(None, alias="user.name")
    user_domain: str | None = Field(None, alias="user.domain")

    model_config = {"populate_by_name": True, "extra": "allow"}

    def to_dict(self) -> dict[str, Any]:
        data = {
            "host.name": self.host_name,
            "host.domain": self.host_domain,
            "host.ip": self.host_ip,
            "user.name": self.user_name,
            "user.domain": self.user_domain,
        }
        if self.model_extra:
            data.update(self.model_extra)
        return data


class PlaybookStep(BaseModel):
    """Один шаг сценария атаки."""
    id: str
    template: str                              # Имя Jinja2-шаблона (без расширения)
    delay_from_start: str | None = None        # "0s", "2m", "1h"
    delay_from_prev: str | None = None         # Задержка от предыдущего шага
    depends_on: str | None = None              # ID родительского шага
    fields: dict[str, Any] = Field(default_factory=dict)
    description: str | None = None
    multiplier: int = Field(default=1, ge=1)

    @field_validator("delay_from_start", "delay_from_prev", mode="before")
    @classmethod
    def coerce_delay_to_str(cls, v: Any) -> str | None:
        return str(v) if v is not None else None

    def delay_seconds(self) -> float:
        """Парсинг задержки в секунды. Приоритет: delay_from_prev, delay_from_start."""
        raw = self.delay_from_prev or self.delay_from_start or "0s"
        return _parse_duration(raw)


class Playbook(BaseModel):
    """Полный сценарий атаки."""
    name: str
    description: str | None = None
    mitre_tactics: list[str] = Field(default_factory=list)
    mitre_techniques: list[str] = Field(default_factory=list)
    global_context: GlobalContext = Field(default_factory=GlobalContext)
    steps: list[PlaybookStep] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_depends_on(self) -> "Playbook":
        step_ids = {s.id for s in self.steps}
        for step in self.steps:
            if step.depends_on and step.depends_on not in step_ids:
                raise ValueError(
                    f"Step '{step.id}' depends_on '{step.depends_on}' "
                    f"which does not exist. Known IDs: {sorted(step_ids)}"
                )
        return self

    def execution_order(self) -> list[PlaybookStep]:
        """
        Топологическая сортировка шагов с учётом depends_on.
        Шаги без зависимостей идут первыми.
        """
        order: list[PlaybookStep] = []
        visited: set[str] = set()
        step_map = {s.id: s for s in self.steps}

        def visit(step_id: str) -> None:
            if step_id in visited:
                return
            visited.add(step_id)
            step = step_map[step_id]
            if step.depends_on:
                visit(step.depends_on)
            order.append(step)

        for s in self.steps:
            visit(s.id)
        return order


# ------------------------------------------------------------------ #
# Parser                                                               #
# ------------------------------------------------------------------ #

class PlaybookParser:
    """Загружает и валидирует YAML-файл сценария."""

    @staticmethod
    def from_file(path: str | Path) -> Playbook:
        """Загрузить Playbook из YAML-файла."""
        text = Path(path).read_text(encoding="utf-8")
        return PlaybookParser.from_yaml(text)

    @staticmethod
    def from_yaml(yaml_text: str) -> Playbook:
        """Разобрать Playbook из YAML-строки."""
        yaml_text = yaml_text.strip()
        if yaml_text.startswith("```yaml"):
            yaml_text = yaml_text[7:]
        elif yaml_text.startswith("```"):
            yaml_text = yaml_text[3:]
        if yaml_text.endswith("```"):
            yaml_text = yaml_text[:-3]
            
        data = yaml.safe_load(yaml_text)
        if not isinstance(data, dict):
            raise ValueError("YAML must be a dictionary")
        return PlaybookParser.from_dict(data)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Playbook:
        """Разобрать Playbook из словаря."""
        if "playbook" in data and isinstance(data["playbook"], dict):
            data = data["playbook"]
        return Playbook.model_validate(data)

    @staticmethod
    def to_yaml(playbook: Playbook) -> str:
        """Сериализовать Playbook обратно в YAML."""
        data = playbook.model_dump(exclude_none=True, by_alias=True)
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)


# ------------------------------------------------------------------ #
# Duration parser                                                      #
# ------------------------------------------------------------------ #

_DURATION_PATTERN = re.compile(
    r"(?:(?P<days>\d+)d)?"
    r"(?:(?P<hours>\d+)h)?"
    r"(?:(?P<minutes>\d+)m)?"
    r"(?:(?P<seconds>\d+(?:\.\d+)?)s)?",
    re.IGNORECASE,
)


def _parse_duration(raw: str) -> float:
    """
    Парсинг строки задержки в секунды.
    Примеры: "0s" → 0.0, "15s" → 15.0, "2m" → 120.0, "1h30m" → 5400.0, "3d" → 259200.0
    """
    raw = raw.strip()
    if not raw or raw in ("0", "0s"):
        return 0.0

    m = _DURATION_PATTERN.fullmatch(raw)
    if not m or not any(m.group(g) for g in ("days", "hours", "minutes", "seconds")):
        raise ValueError(f"Cannot parse duration: '{raw}'. Expected format like '15s', '2m', '1h30m', '3d'")

    total = 0.0
    if m.group("days"):
        total += int(m.group("days")) * 86400
    if m.group("hours"):
        total += int(m.group("hours")) * 3600
    if m.group("minutes"):
        total += int(m.group("minutes")) * 60
    if m.group("seconds"):
        total += float(m.group("seconds"))
    return total
