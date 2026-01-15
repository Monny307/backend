"""add_cv_keywords_table

Revision ID: bbe01a798935
Revises: 7f95b1b98e8a
Create Date: 2026-01-15 16:05:50.597448

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'bbe01a798935'
down_revision = '7f95b1b98e8a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('cv_keywords',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cv_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('keywords', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('extraction_method', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['cv_id'], ['cvs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('cv_keywords')
