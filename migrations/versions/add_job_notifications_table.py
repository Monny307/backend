"""add job notifications table

Revision ID: add_job_notifications_001
Revises: bbe01a798935
Create Date: 2026-01-15 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_job_notifications_001'
down_revision = 'bbe01a798935'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('job_notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cv_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('matched_keywords', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['cv_id'], ['cvs.id'], ),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_job_notifications_user_id'), 'job_notifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_job_notifications_notification_type'), 'job_notifications', ['notification_type'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_job_notifications_notification_type'), table_name='job_notifications')
    op.drop_index(op.f('ix_job_notifications_user_id'), table_name='job_notifications')
    op.drop_table('job_notifications')
