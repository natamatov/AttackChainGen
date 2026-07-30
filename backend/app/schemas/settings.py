from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class SettingBase(BaseModel):
    key: str
    value: Optional[str] = None
    description: Optional[str] = None

class SettingCreate(SettingBase):
    pass

class SettingUpdate(SettingBase):
    pass

class SettingInDB(SettingBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SettingsUpdateBulk(BaseModel):
    settings: List[SettingUpdate]
