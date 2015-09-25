"""Change the type of the subscriptions.uri column to UnicodeText().

Revision ID: 426c77c1b30c
Revises: ef3059e0396
Create Date: 2015-09-25 12:26:18.283347

"""

# revision identifiers, used by Alembic.
revision = '426c77c1b30c'
down_revision = 'b0bf0fbf353'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_index('subs_uri_idx_subscriptions')
    with op.batch_alter_table('subscriptions') as batch_op:
        batch_op.alter_column('uri', type_=sa.types.UnicodeText)
    op.create_index('subs_uri_idx_subscriptions', 'subscriptions', ['uri'])


def downgrade():
    # Don't support downgrading as this would mean changing the column type
    # back to Unicode(256) which we wouldn't be able to do if for example some
    # values longer than 256 characters had been inserted.
    pass
