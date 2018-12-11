"""
Fix FK constraint cascade behaviour.

Revision ID: dfb8b45674db
Revises: dba81a22ea75
Create Date: 2017-07-18 13:32:04.515830
"""

from __future__ import unicode_literals

from alembic import op
from sqlalchemy.dialects import postgresql

revision = "dfb8b45674db"
down_revision = "dba81a22ea75"


def upgrade():
    op.drop_constraint(
        "fk__authzcode__authclient_id__authclient", "authzcode", type_="foreignkey"
    )
    op.drop_constraint("fk__authzcode__user_id__user", "authzcode", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk__authzcode__user_id__user"),
        "authzcode",
        "user",
        ["user_id"],
        ["id"],
        ondelete="cascade",
    )
    op.create_foreign_key(
        op.f("fk__authzcode__authclient_id__authclient"),
        "authzcode",
        "authclient",
        ["authclient_id"],
        ["id"],
        ondelete="cascade",
    )


def downgrade():
    op.drop_constraint(
        op.f("fk__authzcode__authclient_id__authclient"),
        "authzcode",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk__authzcode__user_id__user"), "authzcode", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk__authzcode__user_id__user", "authzcode", "user", ["user_id"], ["id"]
    )
    op.create_foreign_key(
        "fk__authzcode__authclient_id__authclient",
        "authzcode",
        "authclient",
        ["authclient_id"],
        ["id"],
    )
