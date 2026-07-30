from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List

from app.db.base import get_db
from app.db.models import User, StudentAssignment, SimulationRun, AssignmentStatus, UserRole
from app.api.deps import get_current_user
from app.schemas.assignment import AssignmentCreate, AssignmentResponse, AssignmentSubmit

router = APIRouter(prefix="/assignments", tags=["Assignments"])

@router.get("/", response_model=List[AssignmentResponse])
async def get_assignments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.STUDENT:
        # Students see only their own assignments
        stmt = select(StudentAssignment).where(StudentAssignment.assigned_to == current_user.id).order_by(StudentAssignment.created_at.desc())
    else:
        # Instructors/Admins see all
        stmt = select(StudentAssignment).order_by(StudentAssignment.created_at.desc())
        
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/", response_model=AssignmentResponse)
async def create_assignment(
    assignment: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Not enough privileges")
        
    # Check if simulation exists
    sim_stmt = select(SimulationRun).where(SimulationRun.id == assignment.simulation_id)
    sim_result = await db.execute(sim_stmt)
    sim = sim_result.scalar_one_or_none()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")

    new_assign = StudentAssignment(
        simulation_id=assignment.simulation_id,
        assigned_to=assignment.assigned_to,
        assigned_by=current_user.id,
        legend=assignment.legend
    )
    
    db.add(new_assign)
    await db.commit()
    await db.refresh(new_assign)
    return new_assign

@router.post("/{assignment_id}/submit", response_model=AssignmentResponse)
async def submit_assignment(
    assignment_id: int,
    submission: AssignmentSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(StudentAssignment).options(selectinload(StudentAssignment.simulation_run)).where(StudentAssignment.id == assignment_id)
    result = await db.execute(stmt)
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
        
    if current_user.role == UserRole.STUDENT and assignment.assigned_to != current_user.id:
        raise HTTPException(status_code=403, detail="Not your assignment")

    if assignment.status == AssignmentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Assignment already completed")

    sim = assignment.simulation_run
    if not sim or not sim.artifacts:
        assignment.status = AssignmentStatus.FAILED
        assignment.submitted_answers = submission.answers
        await db.commit()
        raise HTTPException(status_code=400, detail="Simulation has no artifacts to check against")

    artifacts = sim.artifacts
    
    # Check answers
    # We expect the submission.answers dict to match the keys of artifacts
    # Example artifacts: {"C2 IP": "10.0.0.5", "Malicious Process": "powershell.exe"}
    
    correct_count = 0
    total_required = len(artifacts)
    
    for key, expected_val in artifacts.items():
        if key in submission.answers:
            # Case insensitive check, strip whitespace
            submitted_val = str(submission.answers[key]).strip().lower()
            exp_val = str(expected_val).strip().lower()
            if submitted_val == exp_val:
                correct_count += 1

    assignment.submitted_answers = submission.answers

    if total_required > 0 and correct_count == total_required:
        assignment.status = AssignmentStatus.COMPLETED
        assignment.score = 100
    else:
        assignment.status = AssignmentStatus.FAILED
        assignment.score = 0
        
    await db.commit()
    await db.refresh(assignment)
    return assignment
