"""Remove the 512-character limit from the nipsa.userid column.

Revision ID: 3db0bed0e78
Revises: 426c77c1b30c
Create Date: 2015-09-25 15:29:32.917634

"""

# revision identifiers, used by Alembic.
revision = '3db0bed0e78'
down_revision = '426c77c1b30c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('nipsa') as batch_op:
        batch_op.alter_column('userid', type_=sa.types.UnicodeText)


def downgrade():
    # Don't support downgrading as this would mean changing the column type
    # back to Unicode(512) which we wouldn't be able to do if for example some
    # values longer than 512 characters had been inserted.
    pass
