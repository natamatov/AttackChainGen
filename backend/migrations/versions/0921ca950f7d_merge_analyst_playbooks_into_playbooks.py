"""merge analyst_playbooks into playbooks

Revision ID: 0921ca950f7d
Revises: f345a957dd06
Create Date: 2026-07-22 12:10:31.081481

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0921ca950f7d'
down_revision: Union[str, Sequence[str], None] = 'f345a957dd06'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add analyst_guide column to playbooks
    op.add_column('playbooks', sa.Column('analyst_guide', sa.Text(), nullable=True))
    
    # Check if analyst_playbooks exists before dropping it (for fresh DBs)
    conn = op.get_bind()
    has_table = conn.dialect.has_table(conn, 'analyst_playbooks')
    if has_table:
        op.drop_table('analyst_playbooks')


def downgrade() -> None:
    # 1. Recreate analyst_playbooks
    op.create_table(
        'analyst_playbooks',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('playbook_id', sa.Integer(), sa.ForeignKey('playbooks.id', ondelete='SET NULL'), nullable=True),
        sa.Column('analyst_guide', sa.Text(), nullable=True),
        sa.Column('investigation_checklist', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # 2. Move data back (just dumping everything into analyst_guide)
    op.execute("""
        INSERT INTO analyst_playbooks (name, playbook_id, analyst_guide)
        SELECT name, id, analyst_guide
        FROM playbooks
        WHERE analyst_guide IS NOT NULL AND analyst_guide != ''
    """)
    
    # 3. Drop column from playbooks
    op.drop_column('playbooks', 'analyst_guide')
