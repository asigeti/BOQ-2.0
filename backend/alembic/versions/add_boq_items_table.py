"""add boq_items table

Revision ID: add_boq_items
Revises:
Create Date: 2025-01-04

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_boq_items'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'boq_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=True),
        sa.Column('chapter_code', sa.String(length=10), nullable=False),
        sa.Column('chapter_name_he', sa.String(length=200), nullable=False),
        sa.Column('chapter_name_en', sa.String(length=200), nullable=True),
        sa.Column('item_code', sa.String(length=50), nullable=False),
        sa.Column('description_he', sa.Text(), nullable=False),
        sa.Column('description_en', sa.Text(), nullable=True),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('total_price', sa.Float(), nullable=False),
        sa.Column('source_filename', sa.String(length=500), nullable=True),
        sa.Column('source_layer', sa.String(length=500), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('user_notes', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), default=False),
        sa.Column('is_modified', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plan_id'], ['project_plans.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_boq_items_id'), 'boq_items', ['id'], unique=False)
    op.create_index(op.f('ix_boq_items_project_id'), 'boq_items', ['project_id'], unique=False)
    op.create_index(op.f('ix_boq_items_chapter_code'), 'boq_items', ['chapter_code'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_boq_items_chapter_code'), table_name='boq_items')
    op.drop_index(op.f('ix_boq_items_project_id'), table_name='boq_items')
    op.drop_index(op.f('ix_boq_items_id'), table_name='boq_items')
    op.drop_table('boq_items')
