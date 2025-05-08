
"""create initial tables

Revision ID: create_initial_tables
Revises: 
Create Date: 2024-01-30 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_initial_tables'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )

    # Create comics table
    op.create_table('comics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('prompt', sa.String(length=500), nullable=False),
        sa.Column('prompt_data_info', postgresql.JSON(), nullable=True),
        sa.Column('topic', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('story_text', sa.String(length=5000), nullable=True),
        sa.Column('data_info', postgresql.JSON(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('story_search_vector', sa.String(), nullable=True),
        sa.Column('view_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('like_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('search_vector', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create panels table
    op.create_table('panels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('comic_id', sa.Integer(), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('text_content', sa.String(length=500), nullable=True),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('image_url', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['comic_id'], ['comics.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_comic_sequence', 'panels', ['comic_id', 'sequence'])

    # Create likes table
    op.create_table('likes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('comic_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['comic_id'], ['comics.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create views table
    op.create_table('views',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('comic_id', sa.Integer(), nullable=False),
        sa.Column('viewed_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['comic_id'], ['comics.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('views')
    op.drop_table('likes')
    op.drop_index('idx_comic_sequence', table_name='panels')
    op.drop_table('panels')
    op.drop_table('comics')
    op.drop_table('users')
