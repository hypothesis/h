"""
Update user unique constraints.

Revision ID: b0e1a12de5e8
Revises: bdaa06b14557
Create Date: 2016-09-08 16:03:59.857402
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "b0e1a12de5e8"
down_revision = "bdaa06b14557"


def upgrade():
    # First we move the existing unique constraint indices out of the way
    op.execute(
        sa.text(
            'ALTER TABLE "user" RENAME CONSTRAINT uq__user__email TO uq__user__email_old'
        )
    )
    op.execute(
        sa.text(
            'ALTER TABLE "user" RENAME CONSTRAINT uq__user__uid TO uq__user__uid_old'
        )
    )
    op.execute(
        sa.text(
            'ALTER TABLE "user" RENAME CONSTRAINT uq__user__username TO uq__user__username_old'
        )
    )

    # Then we can generate the new indices in the background
    op.execute("COMMIT")
    op.create_index(
        op.f("uq__user__email"),
        "user",
        ["email", "authority"],
        unique=True,
        postgresql_concurrently=True,
    )
    op.create_index(
        op.f("uq__user__uid"),
        "user",
        ["uid", "authority"],
        unique=True,
        postgresql_concurrently=True,
    )
    op.create_index(
        op.f("uq__user__username"),
        "user",
        ["username", "authority"],
        unique=True,
        postgresql_concurrently=True,
    )

    # Lastly, we can create the constraints using the new indices
    op.execute(
        sa.text(
            'ALTER TABLE "user" ADD CONSTRAINT uq__user__email UNIQUE USING INDEX uq__user__email'
        )
    )
    op.execute(
        sa.text(
            'ALTER TABLE "user" ADD CONSTRAINT uq__user__uid UNIQUE USING INDEX uq__user__uid'
        )
    )
    op.execute(
        sa.text(
            'ALTER TABLE "user" ADD CONSTRAINT uq__user__username UNIQUE USING INDEX uq__user__username'
        )
    )


def downgrade():
    op.drop_constraint("uq__user__email", "user")
    op.drop_constraint("uq__user__uid", "user")
    op.drop_constraint("uq__user__username", "user")

    op.execute(
        sa.text(
            'ALTER TABLE "user" RENAME CONSTRAINT uq__user__email_old TO uq__user__email'
        )
    )
    op.execute(
        sa.text(
            'ALTER TABLE "user" RENAME CONSTRAINT uq__user__uid_old TO uq__user__uid'
        )
    )
    op.execute(
        sa.text(
            'ALTER TABLE "user" RENAME CONSTRAINT uq__user__username_old TO uq__user__username'
        )
    )
