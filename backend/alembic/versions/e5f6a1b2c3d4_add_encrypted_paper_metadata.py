"""add encrypted_paper_metadata table

Revision ID: e5f6a1b2c3d4
Revises: d4e5f6a1b2c3
Create Date: 2026-08-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e5f6a1b2c3d4'
down_revision: Union[str, None] = 'd4e5f6a1b2c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'encrypted_paper_metadata',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('question_paper_id', sa.UUID(), nullable=False),
        sa.Column('key_identifier', sa.String(length=255), nullable=False),
        sa.Column('encryption_algorithm', sa.String(length=50), nullable=False),
        sa.Column('nonce', sa.String(length=255), nullable=False),
        sa.Column('wrapped_key', sa.Text(), nullable=False),
        sa.Column('encrypted_storage_path', sa.String(length=1000), nullable=False),
        sa.Column('encryption_version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['question_paper_id'], ['question_papers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_encrypted_paper_metadata_id'), 'encrypted_paper_metadata', ['id'], unique=False)
    op.create_index(op.f('ix_encrypted_paper_metadata_question_paper_id'), 'encrypted_paper_metadata', ['question_paper_id'], unique=True)
    op.create_index(op.f('ix_encrypted_paper_metadata_key_identifier'), 'encrypted_paper_metadata', ['key_identifier'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_encrypted_paper_metadata_key_identifier'), table_name='encrypted_paper_metadata')
    op.drop_index(op.f('ix_encrypted_paper_metadata_question_paper_id'), table_name='encrypted_paper_metadata')
    op.drop_index(op.f('ix_encrypted_paper_metadata_id'), table_name='encrypted_paper_metadata')
    op.drop_table('encrypted_paper_metadata')
