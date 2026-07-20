"""
Pydantic схемы для Stand (стенды Elasticsearch).
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field


class StandCreate(BaseModel):
    name: str = Field(max_length=255)
    description: str | None = None
    elastic_url: str = Field(description="URL Elasticsearch, например https://localhost:9200")
    api_key: str = Field(description="API key в формате 'id:key'")
    index_pattern: str = "logs-attackchain-default"
    verify_ssl: bool = False


class StandUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    elastic_url: str | None = None
    api_key: str | None = None
    index_pattern: str | None = None
    verify_ssl: bool | None = None
    is_active: bool | None = None


class StandOut(BaseModel):
    id: int
    name: str
    description: str | None
    elastic_url: str
    index_pattern: str
    verify_ssl: bool
    is_active: bool
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StandTestResult(BaseModel):
    connected: bool
    message: str
    cluster_name: str | None = None
    version: str | None = None
