"""
Fill in annotation text_rendered column

Revision ID: d536d9a342f3
Revises: 39b1935d9e7b
Create Date: 2016-08-10 14:09:01.787927
"""

from __future__ import unicode_literals
from __future__ import print_function

import sys
from collections import namedtuple

from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from h.util import markdown


revision = "d536d9a342f3"
down_revision = "39b1935d9e7b"

Base = declarative_base()
Session = sessionmaker()


class Window(namedtuple("Window", ["start", "end"])):
    pass


class Annotation(Base):
    __tablename__ = "annotation"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    updated = sa.Column(sa.DateTime)

    text = sa.Column(sa.UnicodeText)
    text_rendered = sa.Column(sa.UnicodeText)


def upgrade():
    session = Session(bind=op.get_bind())

    fill_annotations_text_rendered(session)


def downgrade():
    pass


def fill_annotations_text_rendered(session):
    windows = _fetch_windows(session)
    session.rollback()

    for window in windows:
        _fill_annotation_window_text_rendered(session, window)
        session.commit()

        print(".", end="")
        sys.stdout.flush()


def _fill_annotation_window_text_rendered(session, window):
    query = (
        session.query(Annotation)
        .filter(Annotation.updated.between(window.start, window.end))
        .order_by(Annotation.updated.asc())
    )

    for a in query:
        a.text_rendered = markdown.render(a.text)


def _fetch_windows(session, chunksize=100):
    updated = (
        session.query(Annotation.updated)
        .execution_options(stream_results=True)
        .order_by(Annotation.updated.desc())
        .all()
    )

    count = len(updated)
    windows = [
        Window(
            start=updated[min(x + chunksize, count) - 1].updated, end=updated[x].updated
        )
        for x in xrange(0, count, chunksize)
    ]

    return windows
