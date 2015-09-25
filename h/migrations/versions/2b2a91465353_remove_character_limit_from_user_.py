"""Remove the 30-character limit from the user.username column.

Revision ID: 2b2a91465353
Revises: 16c1d19eba5
Create Date: 2015-09-29 14:28:07.189539

"""

# revision identifiers, used by Alembic.
revision = '2b2a91465353'
down_revision = '16c1d19eba5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.alter_column('username', type_=sa.types.UnicodeText)


def downgrade():
    # Don't support downgrading as this would mean changing the column type
    # back to Unicode(30) which we wouldn't be able to do if for example some
    # values longer than 30 characters had been inserted.
    pass
