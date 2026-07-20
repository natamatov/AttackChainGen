"""
Time Drift Engine — управление временными метками событий.

Поддерживает два режима:
  - Real-time:   события генерируются с реальными задержками (sleep между шагами)
  - Historical:  события «в прошлом» — таймстемпы рассчитываются заранее,
                 генерация идёт без пауз (для немедленного расследования)
"""

from __future__ import annotations

import re
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Iterator

from .playbook_parser import PlaybookStep, _parse_duration


class SimulationMode(str, Enum):
    REALTIME = "realtime"
    HISTORICAL = "historical"


class TimeDriftEngine:
    """
    Вычисляет временные метки шагов и управляет задержками выполнения.

    Args:
        mode:            Режим симуляции (realtime / historical)
        backdate_offset: Строка сдвига в прошлое для historical режима.
                         Примеры: "3d", "12h", "30m", "2026-07-01T10:00:00"
    """

    def __init__(
        self,
        mode: SimulationMode = SimulationMode.REALTIME,
        backdate_offset: str | None = None,
    ) -> None:
        self.mode = mode
        self._base_time = self._compute_base_time(backdate_offset)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    @property
    def base_time(self) -> datetime:
        """Время начала симуляции (UTC)."""
        return self._base_time

    def compute_timestamps(self, steps: list[PlaybookStep]) -> list[datetime]:
        """
        Вычислить таймстемп для каждого шага.

        В realtime режиме таймстемп = текущее время в момент выполнения,
        но мы возвращаем запланированные значения относительно base_time.
        В historical режиме все таймстемпы рассчитываются заранее.
        """
        timestamps: list[datetime] = []
        accumulated = 0.0  # секунды от начала

        for step in steps:
            delay = step.delay_seconds()
            accumulated += delay
            ts = self._base_time + timedelta(seconds=accumulated)
            timestamps.append(ts)

        return timestamps

    def wait_before_step(self, step: PlaybookStep, step_index: int) -> None:
        """
        Ожидать нужное время перед выполнением шага.

        В realtime режиме — реальный sleep.
        В historical режиме — без паузы (0 секунд).
        """
        if self.mode == SimulationMode.HISTORICAL:
            return  # Генерируем мгновенно

        delay = step.delay_seconds()
        if delay > 0:
            time.sleep(delay)

    def step_iterator(
        self,
        steps: list[PlaybookStep],
    ) -> Iterator[tuple[PlaybookStep, datetime]]:
        """
        Итератор по шагам с автоматическими задержками.

        Yields:
            (step, timestamp) — шаг и его временная метка.
        """
        timestamps = self.compute_timestamps(steps)
        for i, (step, ts) in enumerate(zip(steps, timestamps)):
            self.wait_before_step(step, i)
            # В realtime — корректируем timestamp на реальное текущее время
            actual_ts = datetime.now(timezone.utc) if self.mode == SimulationMode.REALTIME else ts
            yield step, actual_ts

    # ------------------------------------------------------------------ #
    # Private                                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _compute_base_time(backdate_offset: str | None) -> datetime:
        """
        Вычислить базовое время симуляции.

        - None / пустая строка → текущее UTC время
        - "3d" → 3 дня назад
        - "12h" → 12 часов назад
        - "2026-07-01T10:00:00" → конкретная дата (UTC)
        """
        now = datetime.now(timezone.utc)

        if not backdate_offset:
            return now

        # Попытка распарсить как ISO datetime
        iso_pattern = re.compile(
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
        )
        if iso_pattern.match(backdate_offset):
            try:
                dt = datetime.fromisoformat(backdate_offset)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                pass

        # Парсинг как длительности назад
        try:
            seconds = _parse_duration(backdate_offset)
            return now - timedelta(seconds=seconds)
        except ValueError:
            raise ValueError(
                f"Cannot parse backdate_offset: '{backdate_offset}'. "
                "Expected '3d', '12h', '30m', '15s' or ISO datetime string."
            )
