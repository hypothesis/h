"""Reusable mixins for SQLAlchemy declarative models."""

import datetime

import sqlalchemy as sa


class Timestamps:
    created = sa.Column(
        sa.DateTime,
        default=datetime.datetime.utcnow,
        server_default=sa.func.now(),  # pylint:disable=not-callable
        nullable=False,
    )
    updated = sa.Column(
        sa.DateTime,
        server_default=sa.func.now(),  # pylint:disable=not-callable
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )
