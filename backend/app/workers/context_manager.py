"""
Context Manager — ядро генератора AttackChainGen.

Отвечает за:
  - хранение глобального контекста инцидента (артефакты: PID, IP, пользователи)
  - передачу артефактов между шагами цепочки (depends_on)
  - генерацию случайных реалистичных артефактов через Faker
  - разрешение State Binding ({{ step_1.process.pid }})
"""

from __future__ import annotations

import random
import re
from typing import Any

from faker import Faker

fake = Faker()

# Диапазоны внутренних IP для корпоративных сетей
INTERNAL_NETWORKS = [
    "10.0.{}.{}",
    "10.10.{}.{}",
    "192.168.1.{}",
    "192.168.10.{}",
    "172.16.{}.{}",
]

# Легитимные корпоративные домены (Faker дополняет)
CORP_DOMAINS = [
    "corp.local",
    "internal.company.com",
    "ad.enterprise.net",
    "dc.corp",
]

# Типичные корпоративные имена хостов
HOST_PREFIXES = [
    "DESKTOP", "LAPTOP", "WS", "PC", "CLIENT",
    "SERVER", "SRV", "DC", "FS", "SQL",
]


class ContextManager:
    """
    Управляет состоянием одной симуляции: хранит артефакты,
    резолвит привязки между шагами.
    """

    def __init__(
        self,
        global_context: dict[str, Any] | None = None,
        fake_locale: str = "en_US",
        internal_networks: list[str] | None = None,
        corp_domains: list[str] | None = None,
        real_hostnames: list[str] | None = None,
        real_ips: list[str] | None = None,
    ) -> None:
        self._fake = Faker(fake_locale)
        self._internal_networks = internal_networks or INTERNAL_NETWORKS
        self._corp_domains = corp_domains or CORP_DOMAINS
        # Реальные активы из FictionalEnvironment (если заданы)
        self._real_hostnames: list[str] = real_hostnames or []
        self._real_ips: list[str] = real_ips or []

        # Глобальные переменные инцидента (host, user и т.д.)
        self._global: dict[str, Any] = {}

        # Артефакты по шагам: { step_id: { field_name: value } }
        self._step_artifacts: dict[str, dict[str, Any]] = {}

        # Инициализация глобального контекста
        if global_context:
            self._init_global(global_context)
        else:
            self._init_global({})

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def get_global(self, key: str, default: Any = None) -> Any:
        """Получить глобальную переменную."""
        return self._global.get(key, default)

    def set_step_artifact(self, step_id: str, key: str, value: Any) -> None:
        """Сохранить артефакт шага."""
        self._step_artifacts.setdefault(step_id, {})[key] = value

    def get_step_artifact(self, step_id: str, key: str, default: Any = None) -> Any:
        """Получить артефакт конкретного шага."""
        return self._step_artifacts.get(step_id, {}).get(key, default)

    def get_all_artifacts(self) -> dict[str, dict[str, Any]]:
        """Вернуть все артефакты всех шагов (для итогового отчёта)."""
        return dict(self._step_artifacts)

    def resolve_fields(
        self,
        fields: dict[str, Any],
        step_id: str,
        depends_on: str | None = None,
    ) -> dict[str, Any]:
        """
        Разрешить State Binding в полях шага.

        Поддерживаемые форматы:
          - "{{ step_1.process.pid }}"         — артефакт из другого шага
          - "{{ global.host.name }}"            — глобальная переменная
          - "{{ random.ip_internal }}"          — генерация случайного IP
          - "{{ random.pid }}"                  — случайный PID
          - "{{ random.port }}"                 — случайный порт
          - "{{ random.username }}"             — случайное имя пользователя
          - "{{ random.hostname }}"             — случайное имя хоста
          - "{{ random.domain }}"               — корпоративный домен
          - "{{ random.exe_name }}"             — имя исполняемого файла
          - "{{ random.hash_sha256 }}"          — SHA-256 хэш
          - "{{ random.guid }}"                 — GUID
          - Обычная строка — передаётся как есть
        """
        resolved: dict[str, Any] = {}
        for key, value in fields.items():
            resolved[key] = self._resolve_value(value, step_id, depends_on)
        return resolved

    def build_step_context(
        self,
        step_id: str,
        resolved_fields: dict[str, Any],
        depends_on: str | None = None,
    ) -> dict[str, Any]:
        """
        Собрать итоговый контекст для рендера Jinja2-шаблона:
        глобальные переменные + родительские артефакты + поля шага.
        Автоматически генерирует недостающие значения (pid, tid и т.д.).
        """
        ctx: dict[str, Any] = {}

        # 1. Глобальный контекст
        ctx.update(self._global)

        # 2. Артефакты родительского шага (для depends_on)
        if depends_on and depends_on in self._step_artifacts:
            parent = self._step_artifacts[depends_on]
            ctx["parent_pid"] = parent.get("process_pid")
            ctx["parent_name"] = parent.get("process_name")

        # 3. Поля текущего шага
        ctx.update(resolved_fields)

        # 4. Автогенерация обязательных полей (если не заданы)
        ctx.setdefault("process_pid", self._gen_pid())
        ctx.setdefault("process_tid", self._gen_tid())
        ctx.setdefault("event_id", random.randint(1000, 9999))
        ctx.setdefault("log_id", self._fake.uuid4())

        # 5. Сохранить артефакты шага
        self.set_step_artifact(step_id, "process_pid", ctx.get("process_pid"))
        self.set_step_artifact(step_id, "process_name", ctx.get("process_name"))
        self.set_step_artifact(step_id, "network_dest_ip", ctx.get("destination_ip"))
        self.set_step_artifact(step_id, "network_dest_port", ctx.get("destination_port"))
        self.set_step_artifact(step_id, "file_path", ctx.get("file_path"))
        self.set_step_artifact(step_id, "user_name", ctx.get("user_name") or ctx.get("username"))

        return ctx

    # ------------------------------------------------------------------ #
    # Random generators                                                    #
    # ------------------------------------------------------------------ #

    def gen_internal_ip(self) -> str:
        # Если есть реальные IP из инфраструктуры — используем их
        if self._real_ips:
            return random.choice(self._real_ips)
        tpl = random.choice(self._internal_networks)
        return tpl.format(
            random.randint(1, 254),
            random.randint(1, 254),
        )

    def gen_external_ip(self) -> str:
        # Избегаем внутренних и зарезервированных диапазонов
        while True:
            ip = self._fake.ipv4_public()
            return ip

    def gen_hostname(self) -> str:
        # Если есть реальные хосты из инфраструктуры — используем их
        if self._real_hostnames:
            return random.choice(self._real_hostnames)
        prefix = random.choice(HOST_PREFIXES)
        suffix = random.randint(1, 99)
        dept = random.choice(["HR", "IT", "FIN", "DEV", "MGMT", "SALES"])
        return f"{prefix}-{dept}-{suffix:02d}"

    def gen_corp_domain(self) -> str:
        return random.choice(self._corp_domains)

    def gen_username(self) -> str:
        first = self._fake.first_name().lower()
        last = self._fake.last_name().lower()
        return f"{first[0]}.{last}"

    def gen_sha256(self) -> str:
        return self._fake.sha256()

    def gen_guid(self) -> str:
        return "{" + str(self._fake.uuid4()).upper() + "}"

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _init_global(self, ctx: dict[str, Any]) -> None:
        """Инициализировать глобальный контекст, заполняя пропуски рандомом."""
        for k, v in ctx.items():
            if v is not None:
                self._global[k] = v
                if "." in k:
                    self._global[k.replace(".", "_")] = v

        self._global.setdefault("host_name", ctx.get("host.name") or self.gen_hostname())
        self._global.setdefault("host_domain", ctx.get("host.domain") or self.gen_corp_domain())
        self._global.setdefault("host_ip", ctx.get("host.ip") or self.gen_internal_ip())
        self._global.setdefault("user_name", ctx.get("user.name") or self.gen_username())
        self._global.setdefault("user_domain", ctx.get("user.domain") or self._global.get("host_domain"))
        self._global.setdefault("agent_id", ctx.get("agent.id") or self._fake.uuid4())
        self._global.setdefault("agent_version", ctx.get("agent.version") or "14.0.0")

    def _resolve_value(
        self,
        value: Any,
        step_id: str,
        depends_on: str | None,
    ) -> Any:
        if not isinstance(value, str):
            return value

        # Ищем все {{ ... }} в строке
        pattern = r"\{\{\s*([^}]+?)\s*\}\}"
        matches = re.findall(pattern, value)
        if not matches:
            return value

        result = value
        for match in matches:
            parts = match.strip().split(".")
            replacement = self._resolve_binding(parts, depends_on)
            result = result.replace("{{" + f" {match} " + "}}", str(replacement))
            result = result.replace("{{" + match + "}}", str(replacement))
            # Нормализуем пробелы в шаблоне
            result = re.sub(r"\{\{\s*" + re.escape(match) + r"\s*\}\}", str(replacement), result)

        # Если вся строка — одна подстановка, можно вернуть нестроковый тип
        if len(matches) == 1 and re.fullmatch(pattern, value.strip()):
            parts = matches[0].strip().split(".")
            return self._resolve_binding(parts, depends_on)

        return result

    def _resolve_binding(self, parts: list[str], depends_on: str | None) -> Any:
        namespace = parts[0]

        if namespace == "random":
            return self._resolve_random(parts[1] if len(parts) > 1 else "")

        if namespace == "global":
            key = "_".join(parts[1:]).replace(".", "_")
            return self._global.get(key, "")

        # Привязка к конкретному шагу: {{ step_1.process.pid }}
        step_id = namespace
        field = "_".join(parts[1:]).replace(".", "_")
        return self._step_artifacts.get(step_id, {}).get(field, "")

    def _resolve_random(self, kind: str) -> Any:
        generators = {
            "ip_internal": self.gen_internal_ip,
            "ip_external": self.gen_external_ip,
            "hostname": self.gen_hostname,
            "domain": self.gen_corp_domain,
            "username": self.gen_username,
            "hash_sha256": self.gen_sha256,
            "guid": self.gen_guid,
            "pid": self._gen_pid,
            "tid": self._gen_tid,
            "port_high": lambda: random.randint(49152, 65535),
            "port_common": lambda: random.choice([80, 443, 8080, 8443, 3389, 445, 22]),
            "port": lambda: random.randint(1024, 65535),
        }
        gen = generators.get(kind)
        return gen() if gen else ""

    @staticmethod
    def _gen_pid() -> int:
        return random.randint(1000, 65535)

    @staticmethod
    def _gen_tid() -> int:
        return random.randint(1000, 65535)
