"""playbook_status

Revision ID: 67b9238f68f1
Revises: 1a7ddd4255e7
Create Date: 2026-07-29 10:38:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '67b9238f68f1'
down_revision: Union[str, Sequence[str], None] = '1a7ddd4255e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # We create the ENUM first
    playbookstatus = postgresql.ENUM('DRAFT', 'TESTING', 'APPROVED', 'REJECTED', name='playbookstatus')
    playbookstatus.create(op.get_bind(), checkfirst=True)

    op.add_column('playbooks', sa.Column('status', sa.Enum('DRAFT', 'TESTING', 'APPROVED', 'REJECTED', name='playbookstatus'), server_default='APPROVED', nullable=False))
    op.create_index(op.f('ix_playbooks_status'), 'playbooks', ['status'], unique=False)
    op.add_column('playbooks', sa.Column('stix_references', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('playbooks', 'stix_references')
    op.drop_index(op.f('ix_playbooks_status'), table_name='playbooks')
    op.drop_column('playbooks', 'status')
    playbookstatus = postgresql.ENUM('DRAFT', 'TESTING', 'APPROVED', 'REJECTED', name='playbookstatus')
    playbookstatus.drop(op.get_bind(), checkfirst=True)
