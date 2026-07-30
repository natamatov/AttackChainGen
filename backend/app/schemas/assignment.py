from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any
from app.db.models import AssignmentStatus

class AssignmentBase(BaseModel):
    legend: Optional[str] = None

class AssignmentCreate(AssignmentBase):
    simulation_id: int
    assigned_to: int

class AssignmentResponse(AssignmentBase):
    id: int
    simulation_id: int
    assigned_to: int
    assigned_by: Optional[int] = None
    status: AssignmentStatus
    score: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class AssignmentSubmit(BaseModel):
    answers: Dict[str, str]
