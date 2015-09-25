"""Remove the 30-character limit from the activation.code column.

Revision ID: 14a8ee5bc8da
Revises: 31d15a585cc0
Create Date: 2015-09-25 18:14:24.152442

"""

# revision identifiers, used by Alembic.
revision = '14a8ee5bc8da'
down_revision = '31d15a585cc0'

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('activation') as batch_op:
        batch_op.alter_column('code', type_=sa.types.UnicodeText)


def downgrade():
    # Don't support downgrading as this would mean changing the column type
    # back to Unicode(30) which we wouldn't be able to do if for example some
    # values longer than 30 characters had been inserted.
    pass
