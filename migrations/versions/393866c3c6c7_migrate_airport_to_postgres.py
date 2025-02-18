"""Migrate airport to postgres

Revision ID: 393866c3c6c7
Revises: fcdff7c3f12a
Create Date: 2025-02-06 20:49:05.075894

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '393866c3c6c7'
down_revision = 'fcdff7c3f12a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('airport',
    sa.Column('icao', sa.String(length=10), nullable=False),
    sa.Column('iata', sa.String(length=10), nullable=True),
    sa.Column('name', sa.String(length=200), nullable=True),
    sa.Column('city', sa.String(length=100), nullable=True),
    sa.Column('country', sa.String(length=100), nullable=True),
    sa.Column('latitude', sa.Float(), nullable=True),
    sa.Column('longitude', sa.Float(), nullable=True),
    sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.PrimaryKeyConstraint('icao')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('airport')
    # ### end Alembic commands ###
