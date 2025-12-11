"""add BOQ hierarchy tables (4-level structure)

Revision ID: add_boq_hierarchy
Revises: add_boq_items
Create Date: 2025-12-09

This migration adds the 4-level Israeli BOQ hierarchy:
- boq_sub_document (תת כתב) - Level 1
- boq_chapter (פרק) - Level 2
- boq_sub_chapter (תת פרק) - Level 3
- boq_items gets new FK to sub_chapter (סעיף) - Level 4

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_boq_hierarchy'
down_revision = 'add_boq_items'
branch_labels = None
depends_on = None


def upgrade():
    # ==========================================================================
    # Create boq_sub_document table (Level 1 - תת כתב)
    # ==========================================================================
    op.create_table(
        'boq_sub_document',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('name_he', sa.String(length=300), nullable=False),
        sa.Column('name_en', sa.String(length=300), nullable=True),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cached_total', sa.Float(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_boq_sub_document_id', 'boq_sub_document', ['id'], unique=False)
    op.create_index('ix_boq_sub_document_project_id', 'boq_sub_document', ['project_id'], unique=False)
    op.create_index('ix_boq_sub_document_code', 'boq_sub_document', ['code'], unique=False)

    # ==========================================================================
    # Create boq_chapter table (Level 2 - פרק)
    # ==========================================================================
    op.create_table(
        'boq_chapter',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sub_document_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('name_he', sa.String(length=300), nullable=False),
        sa.Column('name_en', sa.String(length=300), nullable=True),
        sa.Column('dekel_code', sa.String(length=50), nullable=True),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cached_total', sa.Float(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['sub_document_id'], ['boq_sub_document.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_boq_chapter_id', 'boq_chapter', ['id'], unique=False)
    op.create_index('ix_boq_chapter_sub_document_id', 'boq_chapter', ['sub_document_id'], unique=False)
    op.create_index('ix_boq_chapter_code', 'boq_chapter', ['code'], unique=False)

    # ==========================================================================
    # Create boq_sub_chapter table (Level 3 - תת פרק)
    # ==========================================================================
    op.create_table(
        'boq_sub_chapter',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chapter_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('name_he', sa.String(length=300), nullable=False),
        sa.Column('name_en', sa.String(length=300), nullable=True),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cached_total', sa.Float(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['chapter_id'], ['boq_chapter.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_boq_sub_chapter_id', 'boq_sub_chapter', ['id'], unique=False)
    op.create_index('ix_boq_sub_chapter_chapter_id', 'boq_sub_chapter', ['chapter_id'], unique=False)
    op.create_index('ix_boq_sub_chapter_code', 'boq_sub_chapter', ['code'], unique=False)

    # ==========================================================================
    # Add new columns to boq_items for hierarchy support
    # ==========================================================================
    # Add FK to sub_chapter (links to Level 3)
    op.add_column('boq_items', sa.Column('sub_chapter_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_boq_items_sub_chapter',
        'boq_items', 'boq_sub_chapter',
        ['sub_chapter_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_boq_items_sub_chapter_id', 'boq_items', ['sub_chapter_id'], unique=False)

    # Add section code (item number within sub-chapter)
    op.add_column('boq_items', sa.Column('section_code', sa.String(length=20), nullable=True))

    # Add full hierarchical item code for display/search
    op.add_column('boq_items', sa.Column('full_item_code', sa.String(length=50), nullable=True))
    op.create_index('ix_boq_items_full_item_code', 'boq_items', ['full_item_code'], unique=False)

    # Add Dekel pricing reference
    op.add_column('boq_items', sa.Column('dekel_code', sa.String(length=50), nullable=True))

    # Add Israeli standards reference
    op.add_column('boq_items', sa.Column('standard_reference', sa.String(length=100), nullable=True))

    # ==========================================================================
    # Make legacy columns nullable for backward compatibility
    # ==========================================================================
    # These columns were required but now need to be optional for hierarchical items
    op.alter_column('boq_items', 'chapter_code', nullable=True)
    op.alter_column('boq_items', 'chapter_name_he', nullable=True)
    op.alter_column('boq_items', 'item_code', nullable=True)


def downgrade():
    # Remove new columns from boq_items
    op.drop_index('ix_boq_items_full_item_code', table_name='boq_items')
    op.drop_index('ix_boq_items_sub_chapter_id', table_name='boq_items')
    op.drop_constraint('fk_boq_items_sub_chapter', 'boq_items', type_='foreignkey')
    op.drop_column('boq_items', 'standard_reference')
    op.drop_column('boq_items', 'dekel_code')
    op.drop_column('boq_items', 'full_item_code')
    op.drop_column('boq_items', 'section_code')
    op.drop_column('boq_items', 'sub_chapter_id')

    # Restore NOT NULL on legacy columns
    op.alter_column('boq_items', 'item_code', nullable=False)
    op.alter_column('boq_items', 'chapter_name_he', nullable=False)
    op.alter_column('boq_items', 'chapter_code', nullable=False)

    # Drop hierarchy tables (in reverse order due to FKs)
    op.drop_index('ix_boq_sub_chapter_code', table_name='boq_sub_chapter')
    op.drop_index('ix_boq_sub_chapter_chapter_id', table_name='boq_sub_chapter')
    op.drop_index('ix_boq_sub_chapter_id', table_name='boq_sub_chapter')
    op.drop_table('boq_sub_chapter')

    op.drop_index('ix_boq_chapter_code', table_name='boq_chapter')
    op.drop_index('ix_boq_chapter_sub_document_id', table_name='boq_chapter')
    op.drop_index('ix_boq_chapter_id', table_name='boq_chapter')
    op.drop_table('boq_chapter')

    op.drop_index('ix_boq_sub_document_code', table_name='boq_sub_document')
    op.drop_index('ix_boq_sub_document_project_id', table_name='boq_sub_document')
    op.drop_index('ix_boq_sub_document_id', table_name='boq_sub_document')
    op.drop_table('boq_sub_document')
