"""Add os_type to Playbook

Revision ID: a1b2c3d4e5f6
Revises: 0921ca950f7d
Create Date: 2026-07-22 13:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '0921ca950f7d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add os_type column with default "Windows"
    op.add_column('playbooks', sa.Column('os_type', sa.String(length=50), server_default='Windows', nullable=False))
    
    # Optional: We could parse existing names to set 'Linux' if "Linux" is in name, but server_default handles the constraint.
    # Just in case, let's update those that have "Linux" in the name
    op.execute("UPDATE playbooks SET os_type = 'Linux' WHERE name LIKE '%Linux%'")


def downgrade() -> None:
    op.drop_column('playbooks', 'os_type')
