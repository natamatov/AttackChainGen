"""rename_cidr_to_ip_range

Revision ID: f345a957dd06
Revises: 4574ef6705d8
Create Date: 2026-07-21 05:41:54.999443

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f345a957dd06'
down_revision: Union[str, Sequence[str], None] = '4574ef6705d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('network_zones', 'cidr', new_column_name='ip_range')

def downgrade() -> None:
    op.alter_column('network_zones', 'ip_range', new_column_name='cidr')
