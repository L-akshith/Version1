"""add exams table

Revision ID: f7a2d38e91b4
Revises: e0c52bbd928a
Create Date: 2026-08-09 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f7a2d38e91b4'
down_revision: Union[str, None] = 'e0c52bbd928a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'exams',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('exam_code', sa.String(length=50), nullable=False),
        sa.Column('exam_name', sa.String(length=255), nullable=False),
        sa.Column('conducting_authority', sa.String(length=255), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('exam_date', sa.Date(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exams_id'), 'exams', ['id'], unique=False)
    op.create_index(op.f('ix_exams_exam_code'), 'exams', ['exam_code'], unique=True)
    op.create_index(op.f('ix_exams_status'), 'exams', ['status'], unique=False)
    op.create_index(op.f('ix_exams_created_by'), 'exams', ['created_by'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_exams_created_by'), table_name='exams')
    op.drop_index(op.f('ix_exams_status'), table_name='exams')
    op.drop_index(op.f('ix_exams_exam_code'), table_name='exams')
    op.drop_index(op.f('ix_exams_id'), table_name='exams')
    op.drop_table('exams')
