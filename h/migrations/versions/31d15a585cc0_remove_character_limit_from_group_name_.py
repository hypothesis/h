"""Remove the 100-character limit from the group.name column.

Revision ID: 31d15a585cc0
Revises: 3db0bed0e78
Create Date: 2015-09-25 15:39:37.880905

"""

# revision identifiers, used by Alembic.
revision = '31d15a585cc0'
down_revision = '3db0bed0e78'

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('group') as batch_op:
        batch_op.alter_column('name', type_=sa.types.UnicodeText)


def downgrade():
    # Don't support downgrading as this would mean changing the column type
    # back to Unicode(100) which we wouldn't be able to do if for example some
    # values longer than 100 characters had been inserted.
    pass
