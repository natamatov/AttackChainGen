"""
AttackChainGen CLI -- инструмент командной строки для запуска симуляций.

Использование:
    python cli.py run --playbook playbooks/spearphishing.yaml \\
                      --elastic-url https://localhost:9200 \\
                      --api-key "id:key" \\
                      --mode historical \\
                      --backdate 3d \\
                      --noise medium

    python cli.py list-templates
    python cli.py validate --playbook playbooks/spearphishing.yaml
"""
from __future__ import annotations

import io
import json
import logging
import os
import sys
from pathlib import Path

# Windows UTF-8 fix for terminal output
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import click
import yaml

# Добавляем backend в sys.path
sys.path.insert(0, str(Path(__file__).parent))

from app.workers.context_manager import ContextManager
from app.workers.elastic_exporter import ElasticExporter
from app.workers.noise_generator import NoiseGenerator
from app.workers.playbook_parser import PlaybookParser
from app.workers.template_engine import TemplateEngine
from app.workers.time_drift import SimulationMode, TimeDriftEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("attackchain.cli")

TEMPLATES_DIR = Path(__file__).parent / "templates"


# ─────────────────────────────────────────────────────────────────────── #
# CLI Group                                                                #
# ─────────────────────────────────────────────────────────────────────── #

@click.group()
@click.version_option("0.1.0", prog_name="attackchain-cli")
def cli() -> None:
    """AttackChainGen — генератор синтетических цепочек атак для Elastic Security."""


# ─────────────────────────────────────────────────────────────────────── #
# run command                                                              #
# ─────────────────────────────────────────────────────────────────────── #

@cli.command()
@click.option("--playbook", "-p", required=True, type=click.Path(exists=True), help="Путь к YAML-сценарию")
@click.option("--elastic-url", "-u", required=True, help="URL Elasticsearch (например, https://localhost:9200)")
@click.option("--api-key", "-k", required=True, help="Elasticsearch API key (формат 'id:key')")
@click.option("--index", default="logs-attackchain-default", show_default=True, help="Целевой Data Stream / индекс")
@click.option("--mode", type=click.Choice(["realtime", "historical"]), default="realtime", show_default=True)
@click.option("--backdate", default=None, help="Сдвиг в прошлое для historical режима (3d, 12h, 2026-07-01T10:00:00)")
@click.option("--noise", type=click.Choice(["none", "low", "medium", "high"]), default="none", show_default=True)
@click.option("--override", "-o", multiple=True, metavar="KEY=VALUE", help="Переопределение переменных (например, -o user.name=admin)")
@click.option("--dry-run", is_flag=True, help="Рендерить события без отправки в Elastic")
@click.option("--output", type=click.Path(), default=None, help="Сохранить сгенерированные события в JSON-файл")
@click.option("--no-ssl-verify", is_flag=True, help="Отключить верификацию SSL")
def run(
    playbook: str,
    elastic_url: str,
    api_key: str,
    index: str,
    mode: str,
    backdate: str | None,
    noise: str,
    override: tuple[str, ...],
    dry_run: bool,
    output: str | None,
    no_ssl_verify: bool,
) -> None:
    """Запустить симуляцию атаки из YAML-сценария."""

    click.echo(click.style("\n[!] AttackChainGen -- Simulation Engine", fg="red", bold=True))
    click.echo(click.style("=" * 50, fg="red"))

    # 1. Загрузка и валидация Playbook
    click.echo(f"\n[*] Loading playbook: {playbook}")
    try:
        pb = PlaybookParser.from_file(playbook)
    except Exception as exc:
        click.echo(click.style(f"[FAIL] Failed to parse playbook: {exc}", fg="red"))
        sys.exit(1)

    click.echo(click.style(f"   [OK] {pb.name}", fg="green"))
    click.echo(f"   Steps: {len(pb.steps)} | Tactics: {', '.join(pb.mitre_tactics)}")

    # 2. Переопределение переменных
    overrides: dict[str, str] = {}
    for item in override:
        if "=" not in item:
            click.echo(click.style(f"⚠️  Invalid override format '{item}', expected KEY=VALUE", fg="yellow"))
            continue
        k, v = item.split("=", 1)
        overrides[k.strip()] = v.strip()
    if overrides:
        click.echo(f"   Overrides: {overrides}")

    # 3. Инициализация движков
    global_ctx_dict = pb.global_context.to_dict()
    global_ctx_dict.update(overrides)

    ctx_manager = ContextManager(global_context=global_ctx_dict)
    tpl_engine = TemplateEngine(templates_dir=TEMPLATES_DIR)
    drift_engine = TimeDriftEngine(
        mode=SimulationMode(mode),
        backdate_offset=backdate,
    )

    # 4. Подключение к Elastic (если не dry-run)
    exporter: ElasticExporter | None = None
    if not dry_run:
        click.echo(f"\n[*] Connecting to Elasticsearch: {elastic_url}")
        exporter = ElasticExporter(
            elastic_url=elastic_url,
            api_key=api_key,
            index=index,
            verify_ssl=not no_ssl_verify,
        )
        if not exporter.test_connection():
            click.echo(click.style("[FAIL] Cannot connect to Elasticsearch", fg="red"))
            sys.exit(1)
        click.echo(click.style("   [OK] Connected!", fg="green"))
    else:
        click.echo(click.style("\n[DRY RUN] Events will NOT be sent to Elastic", fg="yellow"))

    # 5. Запуск Noise Generator
    noise_gen: NoiseGenerator | None = None
    if not dry_run and noise != "none" and exporter:
        noise_gen = NoiseGenerator(ctx_manager, tpl_engine, exporter, level=noise)
        noise_gen.start()

    # 6. Выполнение цепочки
    steps_ordered = pb.execution_order()
    all_events: list[dict] = []

    click.echo(f"\n🚀 Starting simulation ({mode} mode)")
    click.echo(f"   Base time: {drift_engine.base_time.isoformat()}")
    click.echo(f"   Noise level: {noise}\n")

    for step, ts in drift_engine.step_iterator(steps_ordered):
        click.echo(click.style(f"  >> Step [{step.id}]", fg="cyan"), nl=False)
        click.echo(f"  template={step.template}  ts={ts.strftime('%H:%M:%S')}")

        # Разрешить bindings + построить контекст
        resolved = ctx_manager.resolve_fields(step.fields, step.id, step.depends_on)
        full_ctx = ctx_manager.build_step_context(step.id, resolved, step.depends_on)

        # Рендер шаблона
        try:
            doc = tpl_engine.render(step.template, full_ctx, timestamp=ts)
        except Exception as exc:
            click.echo(click.style(f"    [FAIL] Render error: {exc}", fg="red"))
            continue

        all_events.append(doc)

        # Отправка
        if not dry_run and exporter:
            try:
                exporter.send_event(doc)
                click.echo(click.style(f"    [OK] Sent to {index}", fg="green"))
            except Exception as exc:
                click.echo(click.style(f"    [WARN] Send failed: {exc}", fg="yellow"))
        else:
            click.echo(click.style("    [DRY] Event rendered", fg="yellow"))

    # 7. Остановка шума
    if noise_gen:
        noise_gen.stop()

    # 8. Артефакты
    artifacts = ctx_manager.get_all_artifacts()
    click.echo(click.style("\n[ARTIFACTS] IoC Cheatsheet:", fg="magenta", bold=True))
    click.echo(click.style("=" * 50, fg="magenta"))
    for step_id, arts in artifacts.items():
        non_null = {k: v for k, v in arts.items() if v is not None}
        if non_null:
            click.echo(f"  [{step_id}]")
            for k, v in non_null.items():
                click.echo(f"    {k}: {click.style(str(v), fg='yellow')}")

    # 9. Сохранение в файл
    if output:
        out_path = Path(output)
        out_path.write_text(json.dumps(all_events, indent=2, default=str), encoding="utf-8")
        click.echo(f"\n[SAVED] Events saved to: {output}")

    click.echo(click.style(f"\n[DONE] Simulation complete! {len(all_events)} events generated.", fg="green", bold=True))

    if exporter:
        exporter.close()


# ─────────────────────────────────────────────────────────────────────── #
# validate command                                                         #
# ─────────────────────────────────────────────────────────────────────── #

@cli.command()
@click.option("--playbook", "-p", required=True, type=click.Path(exists=True))
def validate(playbook: str) -> None:
    """Валидировать YAML-сценарий без запуска симуляции."""
    try:
        pb = PlaybookParser.from_file(playbook)
        click.echo(click.style(f"[OK] Valid playbook: {pb.name}", fg="green"))
        click.echo(f"   Steps: {len(pb.steps)}")
        click.echo(f"   MITRE tactics: {pb.mitre_tactics}")
        order = pb.execution_order()
        click.echo(f"   Execution order: {' -> '.join(s.id for s in order)}")
    except Exception as exc:
        click.echo(click.style(f"[FAIL] Invalid playbook: {exc}", fg="red"))
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────── #
# list-templates command                                                   #
# ─────────────────────────────────────────────────────────────────────── #

@cli.command("list-templates")
def list_templates() -> None:
    """Показать доступные ECS-шаблоны событий."""
    try:
        engine = TemplateEngine(templates_dir=TEMPLATES_DIR)
        templates = engine.list_templates()
        click.echo(click.style("\n[TEMPLATES] Available ECS templates:", fg="cyan", bold=True))
        for t in templates:
            click.echo(f"  - {t}")
        click.echo(f"\nTotal: {len(templates)} templates")
    except Exception as exc:
        click.echo(click.style(f"[FAIL] Error: {exc}", fg="red"))
        sys.exit(1)


if __name__ == "__main__":
    cli()
