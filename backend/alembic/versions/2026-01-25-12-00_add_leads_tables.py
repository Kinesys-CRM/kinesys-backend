"""Add leads, tags, and stage history tables

Revision ID: add_leads_tables
Revises: b598b7cf8942
Create Date: 2026-01-25 12:00:00.000000

"""
from typing import Sequence, Union
import sqlmodel
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_leads_tables'
down_revision: Union[str, Sequence[str], None] = 'b598b7cf8942'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create tags table
    op.create_table('tags',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('color', sqlmodel.sql.sqltypes.AutoString(length=7), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'user_id', name='uq_tag_name_user')
    )
    op.create_index(op.f('ix_tags_id'), 'tags', ['id'], unique=False)
    op.create_index(op.f('ix_tags_user_id'), 'tags', ['user_id'], unique=False)

    # Create leads table
    op.create_table('leads',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('first_name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('last_name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('phone', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column('mobile_no', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column('company', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=True),
        sa.Column('organization', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=True),
        sa.Column('website', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('job_title', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('industry', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('source', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False, server_default='Other'),
        sa.Column('stage', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False, server_default='new'),
        sa.Column('temperature', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False, server_default='cold'),
        sa.Column('lead_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('annual_revenue', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('employee_count', sa.Integer(), nullable=True),
        sa.Column('territory', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('interests', sa.JSON(), nullable=True),
        sa.Column('custom_fields', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('assigned_to', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_leads_id'), 'leads', ['id'], unique=False)
    op.create_index(op.f('ix_leads_user_id'), 'leads', ['user_id'], unique=False)
    op.create_index(op.f('ix_leads_assigned_to'), 'leads', ['assigned_to'], unique=False)
    op.create_index(op.f('ix_leads_stage'), 'leads', ['stage'], unique=False)
    op.create_index(op.f('ix_leads_email'), 'leads', ['email'], unique=False)
    op.create_index(op.f('ix_leads_company'), 'leads', ['company'], unique=False)

    # Create lead_tags junction table
    op.create_table('lead_tags',
        sa.Column('lead_id', sa.Uuid(), nullable=False),
        sa.Column('tag_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('lead_id', 'tag_id')
    )
    op.create_index('ix_lead_tags_lead_id', 'lead_tags', ['lead_id'], unique=False)
    op.create_index('ix_lead_tags_tag_id', 'lead_tags', ['tag_id'], unique=False)

    # Create lead_stage_history table
    op.create_table('lead_stage_history',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('lead_id', sa.Uuid(), nullable=False),
        sa.Column('from_stage', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column('to_stage', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('changed_by', sa.Uuid(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lead_stage_history_id'), 'lead_stage_history', ['id'], unique=False)
    op.create_index(op.f('ix_lead_stage_history_lead_id'), 'lead_stage_history', ['lead_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_lead_stage_history_lead_id'), table_name='lead_stage_history')
    op.drop_index(op.f('ix_lead_stage_history_id'), table_name='lead_stage_history')
    op.drop_table('lead_stage_history')

    op.drop_index('ix_lead_tags_tag_id', table_name='lead_tags')
    op.drop_index('ix_lead_tags_lead_id', table_name='lead_tags')
    op.drop_table('lead_tags')

    op.drop_index(op.f('ix_leads_company'), table_name='leads')
    op.drop_index(op.f('ix_leads_email'), table_name='leads')
    op.drop_index(op.f('ix_leads_stage'), table_name='leads')
    op.drop_index(op.f('ix_leads_assigned_to'), table_name='leads')
    op.drop_index(op.f('ix_leads_user_id'), table_name='leads')
    op.drop_index(op.f('ix_leads_id'), table_name='leads')
    op.drop_table('leads')

    op.drop_index(op.f('ix_tags_user_id'), table_name='tags')
    op.drop_index(op.f('ix_tags_id'), table_name='tags')
    op.drop_table('tags')
