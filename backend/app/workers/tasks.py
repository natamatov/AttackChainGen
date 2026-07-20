"""
Celery Tasks — асинхронное выполнение симуляций.

Основная задача run_simulation:
  1. Загружает Playbook и Stand из БД
  2. Инициализирует Context Manager, Template Engine, Time Drift Engine
  3. Запускает Noise Generator в фоне
  4. Итерируется по шагам, рендерит и отправляет события в Elastic
  5. Публикует прогресс в Redis Pub/Sub (→ WebSocket)
  6. Сохраняет артефакты и обновляет статус в БД
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import redis as redis_sync
from celery import Task
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import NoiseLevel, SimulationMode, SimulationRun, SimulationStatus, Stand, Playbook
from app.workers.celery_app import celery_app
from app.workers.context_manager import ContextManager
from app.workers.elastic_exporter import ElasticExporter
from app.workers.noise_generator import NoiseGenerator
from app.workers.playbook_parser import PlaybookParser
from app.workers.template_engine import TemplateEngine
from app.workers.time_drift import SimulationMode as DriftMode, TimeDriftEngine

logger = logging.getLogger(__name__)
settings = get_settings()

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"

# Redis клиент для Pub/Sub (синхронный, для Celery)
_redis_client: redis_sync.Redis | None = None


def get_redis() -> redis_sync.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis_sync.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


def publish_progress(run_id: int, payload: dict) -> None:
    """Публиковать обновление прогресса в Redis channel."""
    try:
        r = get_redis()
        r.publish(f"simulation:{run_id}", json.dumps(payload))
    except Exception as exc:
        logger.warning("Redis publish failed: %s", exc)


# ─────────────────────────────────────────────────────────────────────── #
# Synchronous DB helpers (Celery workers не используют asyncio по умолч.) #
# ─────────────────────────────────────────────────────────────────────── #

def _get_sync_session() -> Session:
    """Создать синхронную DB-сессию для Celery worker."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    sync_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    engine = create_engine(sync_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def _update_run_status(
    db: Session,
    run: SimulationRun,
    status: SimulationStatus,
    current: int = 0,
    total: int = 0,
    message: str | None = None,
    artifacts: dict | None = None,
    events_sent: int = 0,
    error: str | None = None,
) -> None:
    run.status = status
    run.progress_current = current
    run.progress_total = total
    run.progress_message = message
    if artifacts is not None:
        run.artifacts = artifacts
    run.events_sent = events_sent
    if error:
        run.error_message = error
    if status == SimulationStatus.RUNNING and run.started_at is None:
        run.started_at = datetime.now(timezone.utc)
    if status in (SimulationStatus.COMPLETED, SimulationStatus.FAILED, SimulationStatus.CANCELLED):
        run.completed_at = datetime.now(timezone.utc)
    db.commit()

    # Публикация в Redis
    publish_progress(run.id, {
        "run_id": run.id,
        "status": status.value,
        "progress_current": current,
        "progress_total": total,
        "progress_message": message,
        "events_sent": events_sent,
    })


# ─────────────────────────────────────────────────────────────────────── #
# Main Celery Task                                                          #
# ─────────────────────────────────────────────────────────────────────── #

@celery_app.task(bind=True, name="app.workers.tasks.run_simulation")
def run_simulation(self: Task, run_id: int) -> dict:
    """
    Выполнить симуляцию атаки.

    Args:
        run_id: ID записи SimulationRun в БД.

    Returns:
        Словарь с итогами выполнения.
    """
    db = _get_sync_session()

    try:
        # ── 1. Загрузить SimulationRun ────────────────────────────────
        run = db.get(SimulationRun, run_id)
        if not run:
            logger.error("SimulationRun #%d not found", run_id)
            return {"error": "Run not found"}

        # Обновить celery_task_id
        run.celery_task_id = self.request.id
        db.commit()

        # ── 2. Загрузить Stand и Playbook ─────────────────────────────
        stand = db.get(Stand, run.stand_id)
        playbook_record = db.get(Playbook, run.playbook_id)

        if not stand or not playbook_record:
            _update_run_status(
                db, run, SimulationStatus.FAILED,
                error="Stand or Playbook not found"
            )
            return {"error": "Stand or Playbook not found"}

        _update_run_status(
            db, run, SimulationStatus.RUNNING,
            message="Initializing simulation engine..."
        )

        # ── 3. Парсинг сценария ───────────────────────────────────────
        try:
            pb = PlaybookParser.from_yaml(playbook_record.yaml_content)
        except Exception as exc:
            _update_run_status(
                db, run, SimulationStatus.FAILED,
                error=f"Playbook parse error: {exc}"
            )
            return {"error": str(exc)}

        steps = pb.execution_order()
        total_steps = len(steps)

        _update_run_status(
            db, run, SimulationStatus.RUNNING,
            current=0, total=total_steps,
            message=f"Loaded {total_steps} steps. Connecting to Elastic..."
        )

        # ── 4. Инициализация движков ──────────────────────────────────
        global_ctx = pb.global_context.to_dict()
        if run.overrides:
            global_ctx.update(run.overrides)

        ctx_manager = ContextManager(global_context=global_ctx)
        tpl_engine = TemplateEngine(templates_dir=TEMPLATES_DIR)
        drift_engine = TimeDriftEngine(
            mode=DriftMode(run.mode.value),
            backdate_offset=run.backdate_offset,
        )

        # ── 5. Подключение к Elastic ──────────────────────────────────
        exporter = ElasticExporter(
            elastic_url=stand.elastic_url,
            api_key=stand.api_key,
            username=stand.username,
            password=stand.password,
            tenant_id=stand.tenant_id,
            index=stand.index_pattern,
            verify_ssl=stand.verify_ssl,
        )

        if not exporter.test_connection():
            _update_run_status(
                db, run, SimulationStatus.FAILED,
                error=f"Cannot connect to Elasticsearch at {stand.elastic_url}"
            )
            return {"error": "Elastic connection failed"}

        # ── 6. Запуск Noise Generator ─────────────────────────────────
        noise_gen: NoiseGenerator | None = None
        if run.noise_level != NoiseLevel.NONE:
            noise_gen = NoiseGenerator(
                ctx_manager, tpl_engine, exporter,
                level=run.noise_level.value
            )
            noise_gen.start()
            logger.info("Noise generator started: level=%s", run.noise_level)

        # ── 7. Главный цикл выполнения ────────────────────────────────
        events_sent = 0
        errors: list[str] = []

        for step_idx, (step, ts) in enumerate(drift_engine.step_iterator(steps), start=1):
            # Проверка отмены (через Redis флаг)
            try:
                r = get_redis()
                if r.get(f"cancel:{run_id}") == "1":
                    logger.info("Simulation #%d cancelled", run_id)
                    if noise_gen:
                        noise_gen.stop()
                    _update_run_status(
                        db, run, SimulationStatus.CANCELLED,
                        current=step_idx - 1, total=total_steps,
                        events_sent=events_sent,
                        message="Cancelled by user"
                    )
                    return {"status": "cancelled", "events_sent": events_sent}
            except Exception:
                pass

            _update_run_status(
                db, run, SimulationStatus.RUNNING,
                current=step_idx - 1, total=total_steps,
                events_sent=events_sent,
                message=f"Executing step {step_idx}/{total_steps}: {step.id}"
            )

            try:
                resolved = ctx_manager.resolve_fields(step.fields, step.id, step.depends_on)
                full_ctx = ctx_manager.build_step_context(step.id, resolved, step.depends_on)
                doc = tpl_engine.render(step.template, full_ctx, timestamp=ts)
                exporter.send_event(doc)
                events_sent += 1
                logger.info("Step %s: event sent (ts=%s)", step.id, ts.isoformat())
            except Exception as exc:
                error_msg = f"Step {step.id} failed: {exc}"
                errors.append(error_msg)
                logger.error(error_msg)

        # ── 8. Завершение ─────────────────────────────────────────────
        if noise_gen:
            noise_gen.stop()

        artifacts = ctx_manager.get_all_artifacts()
        # Сериализовать артефакты (убрать None)
        serialized_artifacts = {
            step_id: {k: str(v) for k, v in arts.items() if v is not None}
            for step_id, arts in artifacts.items()
        }

        final_status = SimulationStatus.FAILED if errors else SimulationStatus.COMPLETED
        final_msg = f"Failed with {len(errors)} errors. First: {errors[0]}" if errors else f"Completed: {events_sent}/{total_steps} events sent"

        _update_run_status(
            db, run, final_status,
            current=total_steps, total=total_steps,
            artifacts=serialized_artifacts,
            events_sent=events_sent,
            message=final_msg
        )

        exporter.close()
        db.close()

        logger.info(
            "Simulation #%d complete: %d events sent, %d errors",
            run_id, events_sent, len(errors)
        )
        return {
            "status": "completed",
            "run_id": run_id,
            "events_sent": events_sent,
            "errors": errors,
        }

    except Exception as exc:
        logger.exception("Simulation #%d failed with exception", run_id)
        try:
            _update_run_status(
                db, run, SimulationStatus.FAILED,
                error=f"Unexpected error: {exc}"
            )
        except Exception:
            pass
        db.close()
        raise
