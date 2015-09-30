"""Make activation.{created_by,valid_until} nullable

This will make it easier to remove these columns in a later migration.

Revision ID: b0bf0fbf353
Revises: ef3059e0396
Create Date: 2015-09-30 15:14:03.050955

"""

# revision identifiers, used by Alembic.
revision = 'b0bf0fbf353'
down_revision = 'ef3059e0396'

from alembic import op
import sqlalchemy as sa

def upgrade():
    with op.batch_alter_table('activation') as batch_op:
        batch_op.alter_column('created_by',
                              existing_type=sa.Unicode(length=30),
                              nullable=True)
        batch_op.alter_column('valid_until',
                              existing_type=sa.DateTime,
                              nullable=True)


def downgrade():
    with op.batch_alter_table('activation') as batch_op:
        batch_op.alter_column('valid_until',
                              existing_type=sa.DateTime,
                              nullable=False)
        batch_op.alter_column('created_by',
                              existing_type=sa.Unicode(length=30),
                              nullable=False)
