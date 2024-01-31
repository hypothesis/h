"""
Add authority_provided_id field, index to group.

This will allow clients of the API, in certain circumstances, to set a
unique-to-authority identifier on a group, versus having to use the
service-generated ``pubid``. This ``authority_provided_id`` can be used
to perform certain actions on the group without having to know the
``pubid`` beforehand.

Whereas the ``pubid`` is service-owned and globally unique, this
``authority_provided_id`` is unique per authority and owned by the
caller/client. i.e. authority-bound clients may set their own unique
IDs.

``authority_provided_id`` must be unique per authority; ergo the
unique-enforced index
"""

import sqlalchemy as sa
from alembic import op

revision = "5ed9c8c105f6"
down_revision = "5d256923d642"


def upgrade():
    op.add_column(
        "group", sa.Column("authority_provided_id", sa.UnicodeText(), nullable=True)
    )
    op.execute("COMMIT")
    op.create_index(
        op.f("ix__group__groupid"),
        "group",
        ["authority", "authority_provided_id"],
        postgresql_concurrently=True,
        unique=True,
    )


def downgrade():
    op.drop_index(op.f("ix__group__groupid"))
    op.drop_column("group", "authority_provided_id")
