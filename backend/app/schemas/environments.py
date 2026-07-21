from datetime import datetime
from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────────────── #
# Asset
# ─────────────────────────────────────────────────────────────────────── #
class AssetBase(BaseModel):
    hostname: str = Field(..., description="Имя хоста, например SRV-DC01")
    ip_address: str = Field(..., description="IP-адрес, например 192.168.100.10")
    role: str | None = Field(default=None, description="Роль или описание")

class AssetCreate(BaseModel):
    hostname: str = Field(..., description="Имя хоста, например SRV-DC01")
    ip_address: str | None = Field(default=None, description="IP-адрес. Если не указан, сгенерируется автоматически.")
    role: str | None = Field(default=None, description="Роль или описание")

class AssetUpdate(BaseModel):
    hostname: str | None = None
    ip_address: str | None = None
    role: str | None = None

class AssetOut(AssetBase):
    id: int
    zone_id: int

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────── #
# NetworkZone
# ─────────────────────────────────────────────────────────────────────── #
class NetworkZoneBase(BaseModel):
    name: str = Field(..., description="Название зоны, например Servers")
    ip_range: str = Field(..., description="Диапазон IP, например 192.168.100.10-192.168.100.20")
    description: str | None = None

class NetworkZoneCreate(NetworkZoneBase):
    pass

class NetworkZoneUpdate(BaseModel):
    name: str | None = None
    ip_range: str | None = None
    description: str | None = None

class NetworkZoneOut(NetworkZoneBase):
    id: int
    environment_id: int
    assets: list[AssetOut] = []

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────── #
# FictionalEnvironment
# ─────────────────────────────────────────────────────────────────────── #
class FictionalEnvironmentBase(BaseModel):
    name: str = Field(..., description="Название окружения")
    domain: str = Field(..., description="Домен, например corp.local")
    description: str | None = None

class FictionalEnvironmentCreate(FictionalEnvironmentBase):
    pass

class FictionalEnvironmentUpdate(BaseModel):
    name: str | None = None
    domain: str | None = None
    description: str | None = None

class FictionalEnvironmentOut(FictionalEnvironmentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    zones: list[NetworkZoneOut] = []

    model_config = {"from_attributes": True}
