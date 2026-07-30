"""
FastAPI приложение (entrypoint).
Инициализирует роутеры, CORS, обработку ошибок.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, playbooks, simulations, stands, users, websockets, assignments
from app.core.config import get_settings

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logging.info("AttackChainGen API Starting up...")
    logging.info("MARS API Starting up...")
    yield
    # Shutdown
    logging.info("MARS API Shutting down...")


app = FastAPI(
    title="MARS API",
    description="MARS: Purple Teaming Платформа для непрерывной тренировки аналитиков SOC",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production следует ограничить URL фронтенда
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler (опционально, для кастомных форматов ошибок)
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logging.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


# Подключаем роутеры
from app.api.endpoints import environments, ai_prompt, opencti, settings as settings_router, progress

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(stands.router)
app.include_router(playbooks.router)
app.include_router(simulations.router)
app.include_router(websockets.router)
app.include_router(assignments.router, prefix="/api")
app.include_router(environments.router, prefix="/api/environments", tags=["environments"])
app.include_router(ai_prompt.router, prefix="/api/ai-prompt", tags=["ai_prompt"])
app.include_router(opencti.router, prefix="/api/opencti", tags=["opencti"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["settings"])
app.include_router(progress.router, prefix="/api/progress", tags=["progress"])

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": settings.app_name}
