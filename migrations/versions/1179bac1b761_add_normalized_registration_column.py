"""Add normalized registration column"""

from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = '1179bac1b761'
down_revision = '7692e335697c'
branch_labels = None
depends_on = None

def upgrade():
    # Step 1: Add column as nullable
    with op.batch_alter_table('aircraft', schema=None) as batch_op:
        batch_op.add_column(sa.Column('normalized_registration', sa.String(length=20), nullable=True))

    # Step 2: Backfill existing records
    op.execute(
        "UPDATE aircraft SET normalized_registration = UPPER(REPLACE(registration, '-', '')) WHERE registration IS NOT NULL"
    )

    # Step 3: Set column as NOT NULL
    with op.batch_alter_table('aircraft', schema=None) as batch_op:
        batch_op.alter_column('normalized_registration', nullable=False)

def downgrade():
    with op.batch_alter_table('aircraft', schema=None) as batch_op:
        batch_op.drop_column('normalized_registration')