"""add subjects table

Revision ID: a1b2c3d4e5f6
Revises: f7a2d38e91b4
Create Date: 2026-08-09 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f7a2d38e91b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'subjects',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('exam_id', sa.UUID(), nullable=False),
        sa.Column('subject_code', sa.String(length=50), nullable=False),
        sa.Column('subject_name', sa.String(length=255), nullable=False),
        sa.Column('language', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['exam_id'], ['exams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('exam_id', 'subject_code', name='uq_subject_code_per_exam')
    )
    op.create_index(op.f('ix_subjects_created_by'), 'subjects', ['created_by'], unique=False)
    op.create_index(op.f('ix_subjects_exam_id'), 'subjects', ['exam_id'], unique=False)
    op.create_index(op.f('ix_subjects_id'), 'subjects', ['id'], unique=False)
    op.create_index(op.f('ix_subjects_status'), 'subjects', ['status'], unique=False)
    op.create_index(op.f('ix_subjects_subject_code'), 'subjects', ['subject_code'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_subjects_subject_code'), table_name='subjects')
    op.drop_index(op.f('ix_subjects_status'), table_name='subjects')
    op.drop_index(op.f('ix_subjects_id'), table_name='subjects')
    op.drop_index(op.f('ix_subjects_exam_id'), table_name='subjects')
    op.drop_index(op.f('ix_subjects_created_by'), table_name='subjects')
    op.drop_table('subjects')
