import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import get_settings

settings = get_settings()

async def update_db():
    engine = create_async_engine(str(settings.database_url))
    
    async with engine.begin() as conn:
        try:
            print("Adding 'STUDENT' to userrole enum...")
            await conn.execute(text("ALTER TYPE userrole ADD VALUE 'STUDENT';"))
        except Exception as e:
            print(f"Role 'STUDENT' might already exist: {e}")
            
    async with engine.begin() as conn:
        try:
            print("Adding AssignmentStatus enum...")
            await conn.execute(text("CREATE TYPE assignmentstatus AS ENUM ('PENDING', 'COMPLETED', 'FAILED');"))
        except Exception as e:
            print(f"Enum might already exist: {e}")
            
    async with engine.begin() as conn:
        try:
            print("Creating student_assignments table...")
            await conn.execute(text('''
                CREATE TABLE IF NOT EXISTS student_assignments (
                    id SERIAL PRIMARY KEY,
                    simulation_id INTEGER NOT NULL REFERENCES simulation_runs(id) ON DELETE CASCADE,
                    assigned_to INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    assigned_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    legend TEXT,
                    status assignmentstatus NOT NULL DEFAULT 'PENDING',
                    score INTEGER NOT NULL DEFAULT 0,
                    submitted_answers JSON DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            '''))
            
            await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_student_assignments_id ON student_assignments (id);'))
            await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_student_assignments_simulation_id ON student_assignments (simulation_id);'))
            await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_student_assignments_assigned_to ON student_assignments (assigned_to);'))
            await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_student_assignments_status ON student_assignments (status);'))
            
            print("Database updated successfully.")
        except Exception as e:
            print(f"Error creating table: {e}")
            
if __name__ == "__main__":
    asyncio.run(update_db())
