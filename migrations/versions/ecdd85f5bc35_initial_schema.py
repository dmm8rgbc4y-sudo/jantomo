"""initial schema

Revision ID: ecdd85f5bc35
Revises: 
Create Date: 2025-11-21 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = 'ecdd85f5bc35'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # --- user table ---
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('pin_hash', sa.String(length=128), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # --- schedule table ---
    op.create_table(
        'schedule',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.String(length=10), nullable=False),
        sa.Column('time_type', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE')
    )

    # --- device table ---
    op.create_table(
        'device',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('device_token', sa.String(length=64), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE')
    )

    # --- friend table ---
    op.create_table(
        'friend',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('friend_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['friend_id'], ['user.id'], ondelete='CASCADE')
    )

    # --- friend_request table ---
    op.create_table(
        'friend_request',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('receiver_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['sender_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['receiver_id'], ['user.id'], ondelete='CASCADE')
    )


def downgrade():
    op.drop_table('friend_request')
    op.drop_table('friend')
    op.drop_table('device')
    op.drop_table('schedule')
    op.drop_table('user')
