"""Initial

Revision ID: ae3f02bb6927
Revises: 
Create Date: 2025-02-06 18:10:40.674993

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ae3f02bb6927'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('aircraft',
    sa.Column('registration', sa.String(length=20), nullable=False),
    sa.Column('icao24', sa.String(length=10), nullable=True),
    sa.Column('selcal', sa.String(length=10), nullable=True),
    sa.Column('ac_type', sa.String(length=50), nullable=True),
    sa.Column('operator', sa.String(length=100), nullable=True),
    sa.Column('serial_number', sa.String(length=50), nullable=True),
    sa.Column('year_built', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('name', sa.String(length=100), nullable=True),
    sa.Column('engines', sa.String(length=100), nullable=True),
    sa.Column('model', sa.String(length=50), nullable=True),
    sa.Column('construction_number', sa.Integer(), nullable=True),
    sa.Column('test_reg', sa.String(length=20), nullable=True),
    sa.Column('delivery_date', sa.String(length=20), nullable=True),
    sa.Column('remarks_json', sa.Text(), nullable=True),
    sa.Column('previous_reg_json', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('registration')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('aircraft')
    # ### end Alembic commands ###
