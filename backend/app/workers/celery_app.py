"""
Celery application — конфигурация и создание экземпляра.
"""

from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "attackchain",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    # Сериализация
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Retry политика
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_max_retries=3,

    # Результаты
    result_expires=86400,  # 24 часа

    # Мониторинг (для Flower)
    worker_send_task_events=True,
    task_send_sent_event=True,

    # Prefetch — по 1 задаче (симуляции долгие)
    worker_prefetch_multiplier=1,
)
