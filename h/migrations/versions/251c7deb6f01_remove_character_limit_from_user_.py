"""Remove the 256-character limit from the user.password column.

Revision ID: 251c7deb6f01
Revises: 53dd2be04038
Create Date: 2015-09-29 12:52:33.625482

"""

# revision identifiers, used by Alembic.
revision = '251c7deb6f01'
down_revision = '53dd2be04038'

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.alter_column('password', type_=sa.types.UnicodeText)


def downgrade():
    # Don't support downgrading as this would mean changing the column type
    # back to Unicode(256) which we wouldn't be able to do if for example some
    # values longer than 256 characters had been inserted.
    pass
