"""Add typedesignator

Revision ID: eba5c89ff5df
Revises: 1179bac1b761
Create Date: 2025-02-14 18:39:57.614837

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eba5c89ff5df'
down_revision = '1179bac1b761'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('aircraft', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_aircraft_normalized_registration'), ['normalized_registration'], unique=True)

    with op.batch_alter_table('aircraft_type', schema=None) as batch_op:
        batch_op.add_column(sa.Column('type_designator', sa.String(length=10), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('aircraft_type', schema=None) as batch_op:
        batch_op.drop_column('type_designator')

    with op.batch_alter_table('aircraft', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_aircraft_normalized_registration'))

    # ### end Alembic commands ###
