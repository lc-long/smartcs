"""add soft delete fields to conversations and messages

Revision ID: add_soft_delete
Revises: f8831f0f426b
Create Date: 2026-05-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_soft_delete'
down_revision: Union[str, None] = 'f8831f0f426b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add soft delete fields to conversations table
    op.add_column('conversations', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('conversations', sa.Column('deleted_at', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('conversations', sa.Column('deleted_by', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_conversations_is_deleted'), 'conversations', ['is_deleted'], unique=False)

    # Add soft delete fields to messages table
    op.add_column('messages', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('messages', sa.Column('deleted_at', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('messages', sa.Column('deleted_by', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_messages_is_deleted'), 'messages', ['is_deleted'], unique=False)


def downgrade() -> None:
    # Drop indexes and columns from messages table
    op.drop_index(op.f('ix_messages_is_deleted'), table_name='messages')
    op.drop_column('messages', 'deleted_by')
    op.drop_column('messages', 'deleted_at')
    op.drop_column('messages', 'is_deleted')

    # Drop indexes and columns from conversations table
    op.drop_index(op.f('ix_conversations_is_deleted'), table_name='conversations')
    op.drop_column('conversations', 'deleted_by')
    op.drop_column('conversations', 'deleted_at')
    op.drop_column('conversations', 'is_deleted')