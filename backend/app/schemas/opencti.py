from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MitreMappingBase(BaseModel):
    mitre_id: str
    template_name: str
    description: Optional[str] = None

class MitreMappingCreate(MitreMappingBase):
    pass

class MitreMappingUpdate(BaseModel):
    mitre_id: Optional[str] = None
    template_name: Optional[str] = None
    description: Optional[str] = None

class MitreMappingResponse(MitreMappingBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
