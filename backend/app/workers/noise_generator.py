"""
Noise Generator — параллельный генератор фонового «шума» (легитимных событий).

Запускается в отдельном потоке рядом с основной симуляцией.
Генерирует реалистичные события: браузер, антивирус, Windows Update,
сетевые сессии и т.д. Это затрудняет работу аналитиков SOC,
которые должны найти атаку среди легитимной активности.
"""

from __future__ import annotations

import logging
import random
import threading
import time
from datetime import datetime, timezone
from typing import Any

from .context_manager import ContextManager
from .template_engine import TemplateEngine
from .elastic_exporter import ElasticExporter

logger = logging.getLogger(__name__)

# Настройки интенсивности шума (events per minute)
NOISE_LEVELS = {
    "none": 0,
    "low": 5,
    "medium": 20,
    "high": 60,
}

# Легитимные процессы Windows
LEGIT_PROCESSES = [
    ("chrome.exe", r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    ("firefox.exe", r"C:\Program Files\Mozilla Firefox\firefox.exe"),
    ("MsMpEng.exe", r"C:\ProgramData\Microsoft\Windows Defender\Platform\4.18.24010.12\MsMpEng.exe"),
    ("svchost.exe", r"C:\Windows\System32\svchost.exe"),
    ("explorer.exe", r"C:\Windows\explorer.exe"),
    ("WmiPrvSE.exe", r"C:\Windows\System32\wbem\WmiPrvSE.exe"),
    ("SearchIndexer.exe", r"C:\Windows\system32\SearchIndexer.exe"),
    ("OneDrive.exe", r"C:\Users\user\AppData\Local\Microsoft\OneDrive\OneDrive.exe"),
    ("Teams.exe", r"C:\Users\user\AppData\Local\Microsoft\Teams\current\Teams.exe"),
    ("outlook.exe", r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE"),
    ("TrustedInstaller.exe", r"C:\Windows\servicing\TrustedInstaller.exe"),
    ("wuauclt.exe", r"C:\Windows\system32\wuauclt.exe"),
    ("spoolsv.exe", r"C:\Windows\System32\spoolsv.exe"),
    ("lsass.exe", r"C:\Windows\system32\lsass.exe"),
]

# Публичные IP для легитимных соединений
LEGIT_DESTINATIONS = [
    ("8.8.8.8", 53, "DNS Google"),
    ("1.1.1.1", 53, "DNS Cloudflare"),
    ("104.16.0.0", 443, "Cloudflare CDN"),
    ("13.107.42.14", 443, "Microsoft Teams"),
    ("52.114.128.0", 443, "Microsoft Office 365"),
    ("204.79.197.200", 443, "Bing"),
    ("72.21.81.200", 443, "Amazon AWS"),
    ("216.58.215.0", 443, "Google"),
]


class NoiseGenerator:
    """
    Генератор фонового шума.

    Запускается через start() и останавливается через stop().
    Работает в отдельном потоке (daemon thread).
    """

    def __init__(
        self,
        ctx_manager: ContextManager,
        tpl_engine: TemplateEngine,
        exporter: ElasticExporter,
        level: str = "medium",
    ) -> None:
        self._ctx = ctx_manager
        self._tpl = tpl_engine
        self._exporter = exporter
        self._events_per_minute = NOISE_LEVELS.get(level, NOISE_LEVELS["medium"])
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._generated_count = 0

    @property
    def generated_count(self) -> int:
        return self._generated_count

    def start(self) -> None:
        """Запустить генератор в фоновом потоке."""
        if self._events_per_minute == 0:
            logger.info("Noise generator: level=none, skipping")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="noise-generator",
            daemon=True,
        )
        self._thread.start()
        logger.info(
            "Noise generator started: %d events/min",
            self._events_per_minute,
        )

    def stop(self) -> None:
        """Остановить генератор и дождаться завершения потока."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        logger.info(
            "Noise generator stopped. Generated %d events.",
            self._generated_count,
        )

    # ------------------------------------------------------------------ #
    # Private                                                              #
    # ------------------------------------------------------------------ #

    def _run_loop(self) -> None:
        sleep_interval = 60.0 / self._events_per_minute
        while not self._stop_event.is_set():
            try:
                self._emit_random_noise()
            except Exception as exc:
                logger.warning("Noise generator error: %s", exc)
            self._stop_event.wait(timeout=sleep_interval)

    def _emit_random_noise(self) -> None:
        """Выбрать случайный тип события и отправить в Elastic."""
        event_generators = [
            self._gen_process_creation,
            self._gen_network_connection,
        ]
        weights = [0.6, 0.4]
        gen = random.choices(event_generators, weights=weights, k=1)[0]
        doc = gen()
        if doc:
            self._exporter.send_event(doc)
            self._generated_count += 1

    def _build_base_context(self) -> dict[str, Any]:
        return {
            "host_name": self._ctx.get_global("host_name"),
            "host_domain": self._ctx.get_global("host_domain"),
            "host_ip": self._ctx.get_global("host_ip"),
            "user_name": self._ctx.get_global("user_name"),
            "user_domain": self._ctx.get_global("user_domain"),
            "agent_id": self._ctx.get_global("agent_id"),
            "agent_version": self._ctx.get_global("agent_version"),
        }

    def _gen_process_creation(self) -> dict[str, Any] | None:
        proc_name, proc_path = random.choice(LEGIT_PROCESSES)
        ctx = self._build_base_context()
        ctx.update({
            "process_name": proc_name,
            "process_path": proc_path,
            "process_pid": random.randint(1000, 65000),
            "process_tid": random.randint(1000, 65000),
            "parent_pid": 4,  # System
            "parent_name": "System",
            "process_command_line": proc_path,
            "process_hash_sha256": self._ctx.gen_sha256(),
            "process_hash_md5": self._ctx.gen_sha256()[:32],
            "process_guid": self._ctx.gen_guid(),
            "parent_guid": self._ctx.gen_guid(),
            "is_noise": True,
        })
        try:
            return self._tpl.render(
                "sysmon_event_1",
                ctx,
                timestamp=datetime.now(timezone.utc),
            )
        except Exception:
            return None

    def _gen_network_connection(self) -> dict[str, Any] | None:
        dest_ip, dest_port, _ = random.choice(LEGIT_DESTINATIONS)
        proc_name, proc_path = random.choice(LEGIT_PROCESSES[:5])  # только браузеры
        ctx = self._build_base_context()
        ctx.update({
            "process_name": proc_name,
            "process_path": proc_path,
            "process_pid": random.randint(1000, 65000),
            "process_guid": self._ctx.gen_guid(),
            "network_protocol": "tcp",
            "source_ip": self._ctx.get_global("host_ip"),
            "source_port": random.randint(49152, 65535),
            "destination_ip": dest_ip,
            "destination_port": dest_port,
            "network_direction": "egress",
            "is_noise": True,
        })
        try:
            return self._tpl.render(
                "sysmon_event_3",
                ctx,
                timestamp=datetime.now(timezone.utc),
            )
        except Exception:
            return None
