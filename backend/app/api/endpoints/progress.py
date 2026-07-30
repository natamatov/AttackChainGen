from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models import User, StudentAssignment, AssignmentStatus, UserRole
from app.api.auth import get_current_active_user

router = APIRouter()

class LeaderboardEntry(BaseModel):
    student_id: int
    student_name: str
    email: str
    total_score: int
    tasks_completed: int
    tasks_failed: int
    tasks_pending: int

class ProgressAssignmentEntry(BaseModel):
    assignment_id: int
    student_id: int
    student_name: str
    email: str
    simulation_id: int
    legend: str
    status: str
    score: int
    created_at: str

@router.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Returns a leaderboard of students based on their total score.
    Accessible by instructors/admins, and students (to see where they rank).
    """
    students = db.query(User).filter(User.role == UserRole.STUDENT).all()
    leaderboard = []

    for student in students:
        assignments = db.query(StudentAssignment).filter(StudentAssignment.assigned_to == student.id).all()
        
        total_score = sum(a.score for a in assignments if a.status == AssignmentStatus.COMPLETED)
        tasks_completed = sum(1 for a in assignments if a.status == AssignmentStatus.COMPLETED)
        tasks_failed = sum(1 for a in assignments if a.status == AssignmentStatus.FAILED)
        tasks_pending = sum(1 for a in assignments if a.status == AssignmentStatus.PENDING)

        leaderboard.append(LeaderboardEntry(
            student_id=student.id,
            student_name=student.full_name or "Unknown",
            email=student.email,
            total_score=total_score,
            tasks_completed=tasks_completed,
            tasks_failed=tasks_failed,
            tasks_pending=tasks_pending
        ))

    # Sort descending by total score
    leaderboard.sort(key=lambda x: x.total_score, reverse=True)
    return leaderboard

@router.get("/assignments", response_model=List[ProgressAssignmentEntry])
def get_all_student_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Returns all assignments for all students (Instructor view).
    """
    if current_user.role not in (UserRole.INSTRUCTOR, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to view all assignments")

    assignments = db.query(StudentAssignment).join(User, User.id == StudentAssignment.assigned_to).all()
    result = []
    
    for a in assignments:
        result.append(ProgressAssignmentEntry(
            assignment_id=a.id,
            student_id=a.assigned_to,
            student_name=a.assigned_to_user.full_name or "Unknown",
            email=a.assigned_to_user.email,
            simulation_id=a.simulation_id,
            legend=a.legend or "",
            status=a.status.value,
            score=a.score,
            created_at=a.created_at.isoformat()
        ))

    # Sort newest first
    result.sort(key=lambda x: x.created_at, reverse=True)
    return result
