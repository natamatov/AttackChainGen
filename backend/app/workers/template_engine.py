"""
Template Engine — рендер ECS-совместимых JSON-событий через Jinja2.

Загружает .json.j2 шаблоны из директории templates/, рендерит их
в готовые JSON-документы с полями ECS 8.x.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    select_autoescape,
)

# Директория с шаблонами по умолчанию (относительно этого файла)
DEFAULT_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


class TemplateEngine:
    """
    Шаблонизатор ECS-событий на базе Jinja2.

    Шаблоны — файлы .json.j2 в директории templates/.
    Каждый шаблон рендерится в валидный JSON-документ ECS 8.x.
    """

    def __init__(self, templates_dir: str | Path | None = None) -> None:
        self._tpl_dir = Path(templates_dir or DEFAULT_TEMPLATES_DIR)
        if not self._tpl_dir.exists():
            raise FileNotFoundError(f"Templates directory not found: {self._tpl_dir}")

        self._env = Environment(
            loader=FileSystemLoader(str(self._tpl_dir)),
            autoescape=select_autoescape(disabled_extensions=("j2",)),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Добавляем фильтры
        self._env.filters["tojson"] = json.dumps

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def render(
        self,
        template_name: str,
        context: dict[str, Any],
        timestamp: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Рендерить шаблон с заданным контекстом.

        Args:
            template_name: Имя шаблона без расширения (например, "sysmon_event_1")
                           или полное имя файла ("sysmon_event_1.json.j2").
            context:       Словарь переменных для Jinja2.
            timestamp:     Временная метка события. Если None — текущее UTC время.

        Returns:
            Готовый ECS JSON-документ в виде словаря.
        """
        ts = timestamp or datetime.now(timezone.utc)
        tpl_file = self._resolve_template_name(template_name)

        # Экранируем обратные слеши в Windows-путях, чтобы JSON оставался валидным
        safe_ctx = self._escape_context(context)

        # Добавляем стандартные поля в контекст
        full_ctx = {
            "@timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ts.microsecond // 1000:03d}Z",
            "ecs_version": "8.11.0",
            **safe_ctx,
        }

        try:
            tpl = self._env.get_template(tpl_file)
            rendered = tpl.render(**full_ctx)
        except Exception as exc:
            raise TemplateRenderError(
                f"Failed to render template '{tpl_file}': {exc}"
            ) from exc

        try:
            doc = json.loads(rendered)
            
            # Если шаблон использует {{ '@timestamp' }}, он срендерится в строку "@timestamp"
            # Заменяем её на реальное значение времени
            if doc.get("@timestamp") == "@timestamp":
                doc["@timestamp"] = full_ctx["@timestamp"]
                
        except json.JSONDecodeError as exc:
            raise TemplateRenderError(
                f"Template '{tpl_file}' produced invalid JSON: {exc}\n"
                f"Rendered output:\n{rendered}"
            ) from exc

        return doc

    def list_templates(self) -> list[str]:
        """Список доступных шаблонов (без расширения .json.j2)."""
        return sorted(
            p.stem.replace(".json", "")
            for p in self._tpl_dir.glob("*.json.j2")
        )

    def template_exists(self, name: str) -> bool:
        """Проверить, существует ли шаблон."""
        return (self._tpl_dir / self._resolve_template_name(name)).exists()

    # ------------------------------------------------------------------ #
    # Private                                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _resolve_template_name(name: str) -> str:
        if name.endswith(".json.j2"):
            return name
        if name.endswith(".j2"):
            return name
        return f"{name}.json.j2"

    @staticmethod
    def _escape_context(ctx: dict) -> dict:
        """
        Рекурсивно экранирует обратные слеши в строковых значениях контекста.
        Windows-пути вида C:\\Users\\... корректно попадут в JSON как C:\\\\Users\\\\...
        """
        result = {}
        for k, v in ctx.items():
            if isinstance(v, str):
                # Экранируем \ → \\ для корректного JSON
                result[k] = v.replace("\\", "\\\\")
            elif isinstance(v, dict):
                result[k] = TemplateEngine._escape_context(v)
            else:
                result[k] = v
        return result


class TemplateRenderError(Exception):
    """Ошибка рендера шаблона."""
