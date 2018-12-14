"""
Add AuthClient grant/response type columns

Revision ID: b980b1a8f6af
Revises: 1c995723a271
Create Date: 2017-07-11 11:43:01.120391
"""

from __future__ import unicode_literals

import enum

from alembic import op
import sqlalchemy as sa

revision = "b980b1a8f6af"
down_revision = "1c995723a271"

# N.B. for both grant type and response type we enumerate all valid types for
# each field, even though we will not initially support all the valid
# permutations.
#
# This is simply because changing enum types in Postgres is a bit of a faff,
# so if we can avoid doing that as and when we add support for (e.g.) implicit
# or resource owner credentials (AKA "password") grants, we'll save ourselves
# some pain.


class GrantType(enum.Enum):
    authorization_code = "authorization_code"
    client_credentials = "client_credentials"
    jwt_bearer = "urn:ietf:params:oauth:grant-type:jwt-bearer"
    password = "password"


grant_type = sa.Enum(GrantType, name="authclient_grant_type")


class ResponseType(enum.Enum):
    code = "code"
    token = "token"


response_type = sa.Enum(ResponseType, name="authclient_response_type")


def upgrade():
    grant_type.create(op.get_bind())
    op.add_column("authclient", sa.Column("grant_type", grant_type, nullable=True))

    response_type.create(op.get_bind())
    op.add_column(
        "authclient", sa.Column("response_type", response_type, nullable=True)
    )


def downgrade():
    op.drop_column("authclient", "grant_type")
    grant_type.drop(op.get_bind())

    op.drop_column("authclient", "response_type")
    response_type.drop(op.get_bind())
