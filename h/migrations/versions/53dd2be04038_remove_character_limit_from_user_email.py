"""Remove the 100-character limit from the user.email column.

Revision ID: 53dd2be04038
Revises: 1ca28a20d608
Create Date: 2015-09-29 12:01:37.046660

"""

# revision identifiers, used by Alembic.
revision = '53dd2be04038'
down_revision = '1ca28a20d608'

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.alter_column('email', type_=sa.types.UnicodeText)


def downgrade():
    # Don't support downgrading as this would mean changing the column type
    # back to Unicode(100) which we wouldn't be able to do if for example some
    # values longer than 100 characters had been inserted.
    pass
