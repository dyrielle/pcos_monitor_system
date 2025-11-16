"""add_missing_awareness_and_symptom_items

Revision ID: 74b9a3065316
Revises: 5fc9b5ac97ee
Create Date: 2025-11-16 18:45:05.288865

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '74b9a3065316'
down_revision = '5fc9b5ac97ee'
branch_labels = None
depends_on = None


def upgrade():
    # Add missing awareness items
    op.add_column('student_profiles', sa.Column('awareness_6', sa.Integer(), nullable=True))
    op.add_column('student_profiles', sa.Column('awareness_7', sa.Integer(), nullable=True))
    op.add_column('student_profiles', sa.Column('awareness_8', sa.Integer(), nullable=True))
    
    # Add missing symptom item
    op.add_column('student_profiles', sa.Column('symptoms_6', sa.Integer(), nullable=True))
    
    # Add fatigue item (used in both academic pressure context and symptoms)
    op.add_column('student_profiles', sa.Column('fatigue_sleep_item', sa.Integer(), nullable=True))


def downgrade():
    # Remove columns
    op.drop_column('student_profiles', 'fatigue_sleep_item')
    op.drop_column('student_profiles', 'symptoms_6')
    op.drop_column('student_profiles', 'awareness_8')
    op.drop_column('student_profiles', 'awareness_7')
    op.drop_column('student_profiles', 'awareness_6')
