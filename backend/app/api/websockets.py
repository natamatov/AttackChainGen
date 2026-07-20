"""
WebSocket Progress Hub для трансляции обновлений симуляций.

Слушает Redis Pub/Sub и рассылает сообщения подключённым клиентам (React-frontend).
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redis.asyncio import Redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["websockets"])

# Глобальный менеджер подключений
class ConnectionManager:
    def __init__(self):
        # run_id -> список WebSocket соединений
        self.active_connections: dict[int, list[WebSocket]] = {}
        # Фоновые таски подписки на Redis
        self._redis_tasks: dict[int, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, run_id: int):
        await websocket.accept()
        if run_id not in self.active_connections:
            self.active_connections[run_id] = []
            # Запускаем слушателя Redis для этого run_id
            self._redis_tasks[run_id] = asyncio.create_task(
                self._listen_redis_for_run(run_id)
            )
        self.active_connections[run_id].append(websocket)
        logger.info(f"WebSocket client connected to run_id={run_id}")

    def disconnect(self, websocket: WebSocket, run_id: int):
        if run_id in self.active_connections:
            if websocket in self.active_connections[run_id]:
                self.active_connections[run_id].remove(websocket)
            if not self.active_connections[run_id]:
                # Нет больше клиентов для этого run_id -> отписываемся
                del self.active_connections[run_id]
                task = self._redis_tasks.pop(run_id, None)
                if task:
                    task.cancel()
        logger.info(f"WebSocket client disconnected from run_id={run_id}")

    async def broadcast(self, run_id: int, message: dict[str, Any]):
        if run_id in self.active_connections:
            # Копируем список для безопасной итерации
            for connection in list(self.active_connections[run_id]):
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Error sending to WS client (run {run_id}): {e}")
                    self.disconnect(connection, run_id)

    async def _listen_redis_for_run(self, run_id: int):
        """Слушает Redis Pub/Sub канал для конкретной симуляции."""
        redis = Redis.from_url(settings.redis_url, decode_responses=True)
        pubsub = redis.pubsub()
        channel_name = f"simulation:{run_id}"
        await pubsub.subscribe(channel_name)
        logger.info(f"Subscribed to Redis channel {channel_name}")
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    await self.broadcast(run_id, data)
                    
                    # Если статус конечный, можно завершить подписку
                    status = data.get("status")
                    if status in ("completed", "failed", "cancelled"):
                        logger.info(f"Simulation {run_id} finished ({status}). Closing Redis subscription.")
                        break
        except asyncio.CancelledError:
            logger.info(f"Redis listener task cancelled for run_id={run_id}")
        except Exception as e:
            logger.error(f"Redis listener error for run_id={run_id}: {e}")
        finally:
            await pubsub.unsubscribe(channel_name)
            await redis.aclose()


manager = ConnectionManager()


@router.websocket("/ws/simulations/{run_id}/progress")
async def simulation_progress_ws(websocket: WebSocket, run_id: int):
    """
    WebSocket эндпоинт для получения прогресса симуляции.
    Подключается клиент, мы пробрасываем ему события из Redis.
    """
    await manager.connect(websocket, run_id)
    try:
        while True:
            # Держим соединение открытым. Клиент может пинговать нас.
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, run_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, run_id)
