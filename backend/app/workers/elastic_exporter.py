"""
Elastic Exporter — отправка ECS-документов в Elasticsearch через Bulk API.

Поддерживает:
  - Data Streams (logs-attackchain-default)
  - Retry логика с экспоненциальной задержкой (tenacity)
  - Batch-отправка (Bulk API)
  - Верификация подключения
"""

from __future__ import annotations

import logging
from typing import Any

from elasticsearch import Elasticsearch, BadRequestError, TransportError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

logger = logging.getLogger(__name__)


class ElasticExporter:
    """
    Транспортный модуль для отправки событий в Elasticsearch.

    Args:
        elastic_url:  URL Elasticsearch (например, "https://localhost:9200")
        api_key:      API ключ (формат "id:api_key" или base64 encoded)
        index:        Имя Data Stream или индекса
        verify_ssl:   Проверять SSL сертификат (False для self-signed)
    """

    def __init__(
        self,
        elastic_url: str,
        api_key: str | None = None,
        username: str | None = None,
        password: str | None = None,
        tenant_id: str | None = None,
        index: str = "logs-attackchain-default",
        verify_ssl: bool = False,
    ) -> None:
        self._index = index
        
        client_kwargs = {
            "hosts": [elastic_url],
            "verify_certs": verify_ssl,
            "ssl_show_warn": False,
        }
        
        if api_key:
            client_kwargs["api_key"] = api_key
        elif username and password:
            client_kwargs["basic_auth"] = (username, password)
            
        if tenant_id:
            # For OpenSearch / OpenDistro security
            client_kwargs["headers"] = {
                "securitytenant": tenant_id,
                "Opendistro-Security-Tenant": tenant_id
            }

        self._client = Elasticsearch(**client_kwargs)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def test_connection(self) -> bool:
        """Проверить доступность Elasticsearch."""
        try:
            info = self._client.info()
            logger.info(
                "Elastic connected: cluster=%s version=%s",
                info["cluster_name"],
                info["version"]["number"],
            )
            return True
        except Exception as exc:
            logger.error("Elastic connection failed: %s", exc)
            return False

    def send_event(self, document: dict[str, Any]) -> None:
        """Отправить одно событие."""
        self.send_bulk([document])

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(TransportError),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def send_bulk(self, documents: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Пакетная отправка документов через Bulk API.

        Args:
            documents: Список ECS JSON-документов.

        Returns:
            Ответ Elasticsearch с метриками (items, errors и т.д.)
        """
        if not documents:
            return {"errors": False, "items": []}

        body = []
        for doc in documents:
            body.append({"create": {"_index": self._index}})
            body.append(doc)

        try:
            resp = self._client.bulk(body=body, refresh=False)
        except BadRequestError as exc:
            logger.error("Bulk API bad request: %s", exc)
            raise

        if resp.get("errors"):
            failed = [
                item["create"]
                for item in resp["items"]
                if item.get("create", {}).get("error")
            ]
            err_msg = failed[0].get("error") if failed else "unknown"
            logger.error("Bulk API: %d/%d documents failed. First error: %s", len(failed), len(documents), err_msg)
            raise Exception(f"Elastic Bulk Error: {err_msg}")

        logger.debug(
            "Bulk API: sent %d documents to '%s'",
            len(documents),
            self._index,
        )
        return resp

    def close(self) -> None:
        """Закрыть соединение с Elasticsearch."""
        self._client.close()

    def __enter__(self) -> "ElasticExporter":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
