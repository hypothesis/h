"""create user subsciptions table

Revision ID: 2246cd7f5801
Revises: None
Create Date: 2014-03-14 23:29:48.634081

"""

# revision identifiers, used by Alembic.
revision = '2246cd7f5801'
down_revision = None

import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy.types import TypeDecorator, VARCHAR


class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string.

    Usage::

        JSONEncodedDict(255)

    """

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


def downgrade():
    op.drop_table('user_subscriptions')
    template_enum.drop(op.get_bind(), checkfirst=False)
    type_enum.drop(op.get_bind(), checkfirst=False)
