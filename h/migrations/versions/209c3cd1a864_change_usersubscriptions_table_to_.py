"""Change UserSubscriptions table to Subscriptions

Revision ID: 209c3cd1a864
Revises: 2246cd7f5801
Create Date: 2014-10-24 13:19:15.932243

"""

# revision identifiers, used by Alembic.
revision = '209c3cd1a864'
down_revision = '2246cd7f5801'

import json
from alembic import op
import sqlalchemy as sa
from sqlalchemy.types import TypeDecorator, VARCHAR


class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string.

    Usage::

        JSONEncodedDict(255)

    """
    # pylint: disable=too-many-public-methods
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)

        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

    def python_type(self):
        return dict

template_enum = sa.Enum('reply_notification', 'custom_search',
                        name="subscription_template")
type_enum = sa.Enum('system', 'user',
                    name="subscription_type")


def upgrade():
    op.drop_table('user_subscriptions')
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.INTEGER, primary_key=True),
        sa.Column('uri', sa.Unicode(256), nullable=False),
        sa.Column('template', sa.VARCHAR(64), nullable=False),
        sa.Column('active', sa.BOOLEAN, default=True, nullable=False)
    )


def downgrade():
    op.drop_table('subscriptions')
    op.create_table(
        'user_subscriptions',
        sa.Column('id', sa.INTEGER, primary_key=True),
        sa.Column(
            'username',
            sa.Unicode(30),
            sa.ForeignKey(
                '%s.%s' % ('user', 'username'),
                onupdate='CASCADE',
                ondelete='CASCADE'
            ),
            nullable=False),
        sa.Column('description', sa.VARCHAR(256), default=""),
        sa.Column('template', template_enum, nullable=False,
                  default='custom_search'),
        sa.Column('active', sa.BOOLEAN, default=True, nullable=False),
        sa.Column('query', JSONEncodedDict(4096), nullable=False),
        sa.Column('type', type_enum, nullable=False, default='user'),
    )
