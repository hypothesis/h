# -*- coding: utf-8 -*-

"""Reusable mixins for SQLAlchemy declarative models."""

from __future__ import unicode_literals

import datetime

import sqlalchemy as sa


class Timestamps(object):
    created = sa.Column(
        sa.DateTime,
        default=datetime.datetime.utcnow,
        server_default=sa.func.now(),
        nullable=False,
    )
    updated = sa.Column(
        sa.DateTime,
        server_default=sa.func.now(),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )
