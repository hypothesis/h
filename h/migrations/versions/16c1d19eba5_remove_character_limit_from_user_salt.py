"""Remove the 256-character limit from the user.salt column.

Revision ID: 16c1d19eba5
Revises: 251c7deb6f01
Create Date: 2015-09-29 13:05:24.142188

"""

# revision identifiers, used by Alembic.
revision = '16c1d19eba5'
down_revision = '251c7deb6f01'

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.alter_column('salt', type_=sa.types.UnicodeText)


def downgrade():
    # Don't support downgrading as this would mean changing the column type
    # back to Unicode(256) which we wouldn't be able to do if for example some
    # values longer than 256 characters had been inserted.
    pass
