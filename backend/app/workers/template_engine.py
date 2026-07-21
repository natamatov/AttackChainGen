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

        # Sensible defaults for all common ECS/Windows fields to prevent StrictUndefined errors
        # when the AI forgets to provide them in the playbook fields.
        self.default_context = {
            "process_pid": 1234,
            "process_name": "unknown_process.exe",
            "process_path": "C:\\Windows\\System32\\unknown_process.exe",
            "process_command_line": "unknown_process.exe",
            "parent_pid": 4,
            "parent_name": "System",
            "parent_path": "C:\\Windows\\System32\\System",
            "user_name": "system",
            "user_domain": "WORKGROUP",
            "user_sid": "S-1-5-18",
            "host_name": "DESKTOP-UNKNOWN",
            "host_domain": "WORKGROUP",
            "host_ip": "10.0.0.1",
            "agent_id": "00000000-0000-0000-0000-000000000000",
            "agent_version": "8.11.0",
            "event_id": 4688,
            "is_elevated": False,
            "is_noise": False,
            "mitre_tactic": "Unknown",
            "mitre_technique": "T0000",
            "mitre_technique_name": "Unknown",
            "file_name": "unknown.txt",
            "file_path": "C:\\unknown.txt",
            "file_size": 1024,
            "file_hash_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
            "network_protocol": "tcp",
            "source_ip": "10.0.0.2",
            "source_port": 12345,
            "destination_ip": "8.8.8.8",
            "destination_port": 443,
            "status": "success",
            "outcome": "success",
            "action": "unknown",
            "registry_path": "HKLM\\Software\\Unknown",
            "registry_key": "UnknownKey",
            "registry_value_name": "UnknownValue",
            "registry_value_data": "UnknownData",
            "service_name": "UnknownService",
            "service_state": "running",
            "script_block_text": "Write-Host 'Unknown'",
            "process_hash_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
            "event_code": 1,
            "logon_type": 3,
            "logon_process_name": "User32",
        }

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
        merged_context = self.default_context.copy()
        merged_context.update(context)

        # 1. @timestamp (ECS requirement)
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        merged_context["@timestamp"] = timestamp.strftime("%Y-%m-%dT%H:%M:%S.") + f"{timestamp.microsecond // 1000:03d}Z"
        
        # 2. Hardcoded ecs.version
        merged_context.setdefault("ecs_version", "8.11.0")

        tpl_file = self._resolve_template_name(template_name)

        # Экранируем обратные слеши в Windows-путях, чтобы JSON оставался валидным
        safe_ctx = self._escape_context(merged_context)

        # 3. Load & render template
        try:
            tpl = self._env.get_template(tpl_file)
            rendered = tpl.render(**safe_ctx)
        except Exception as exc:
            raise TemplateRenderError(
                f"Failed to render template '{tpl_file}': {exc}"
            ) from exc

        try:
            doc = json.loads(rendered)
            
            # Если шаблон использует {{ '@timestamp' }}, он срендерится в строку "@timestamp"
            # Заменяем её на реальное значение времени
            if doc.get("@timestamp") == "@timestamp":
                doc["@timestamp"] = merged_context["@timestamp"]
            
            # Добавляем обязательные теги
            tags = doc.get("tags", [])
            if isinstance(tags, list):
                if "attackchain" not in tags:
                    tags.append("attackchain")
                if "attack-simulation" not in tags:
                    tags.append("attack-simulation")
                doc["tags"] = tags

                
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

    TEMPLATE_ALIASES = {
        "process_creation_template": "win_security_4688",
        "network_connection_template": "sysmon_event_3",
        "smb_access_template": "win_security_4624",
        "remote_execution_template": "win_security_4688",
        "file_creation_template": "sysmon_event_11",
        "authentication_template": "win_security_4624",
    }

    @staticmethod
    def _resolve_template_name(name: str) -> str:
        # Убираем расширение, если оно есть, для проверки алиасов
        base_name = name.replace(".json.j2", "").replace(".j2", "")
        # Если ИИ выдумал имя, подменяем на реальный шаблон
        if base_name in TemplateEngine.TEMPLATE_ALIASES:
            base_name = TemplateEngine.TEMPLATE_ALIASES[base_name]
            
        return f"{base_name}.json.j2"

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
