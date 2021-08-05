"""
Add authclient redirect_uri check.

Revision ID: 52a0b2e5a9c2
Revises: a2295c2bbe29
Create Date: 2017-07-26 10:47:38.895306
"""

import enum

import sqlalchemy as sa
from alembic import op

revision = "52a0b2e5a9c2"
down_revision = "a2295c2bbe29"


def upgrade():
    check = "(grant_type != 'authorization_code') OR (redirect_uri IS NOT NULL)"
    op.create_check_constraint("authz_grant_redirect_uri", "authclient", check)


def downgrade():
    op.drop_constraint("ck__authclient__authz_grant_redirect_uri", "authclient")
