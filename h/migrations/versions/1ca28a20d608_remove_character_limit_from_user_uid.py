"""Remove the 30-character limit from the user.uid column.

Revision ID: 1ca28a20d608
Revises: 32efc6033dd1
Create Date: 2015-09-28 13:44:28.970159

"""

# revision identifiers, used by Alembic.
revision = '1ca28a20d608'
down_revision = '32efc6033dd1'

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.alter_column('uid', type_=sa.types.UnicodeText)


def downgrade():
    # Don't support downgrading as this would mean changing the column type
    # back to Unicode(30) which we wouldn't be able to do if for example some
    # values longer than 30 characters had been inserted.
    pass
