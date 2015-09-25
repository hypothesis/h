"""Remove the 50-character limit from the feature.name column.

Revision ID: 2337185eae43
Revises: 2b2a91465353
Create Date: 2015-09-29 14:42:02.561468

"""

# revision identifiers, used by Alembic.
revision = '2337185eae43'
down_revision = '2b2a91465353'

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('feature') as batch_op:
        batch_op.alter_column('name', type_=sa.types.Text)


def downgrade():
    # Don't support downgrading as this would mean changing the column type
    # back to String(50) which we wouldn't be able to do if for example some
    # values longer than 50 characters had been inserted.
    pass
