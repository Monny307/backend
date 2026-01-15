"""Add saved_jobs table

Revision ID: b1b7c68c41a2
Revises: f768987e2f18
Create Date: 2026-01-14 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'b1b7c68c41a2'
down_revision = 'f768987e2f18'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'saved_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('user_id', 'job_id', name='unique_user_saved_job'),
    )


def downgrade():
    op.drop_table('saved_jobs')
