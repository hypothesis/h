"""
Add the __default__ organization if it doesn't already exist.

Revision ID: 8a7f31c4525d
Revises: 46a22db075d5
Create Date: 2018-03-27 16:50:20.959215

"""
import logging

import sqlalchemy as sa
from alembic import op
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

revision = "8a7f31c4525d"
down_revision = "46a22db075d5"


log = logging.getLogger(__name__)


Base = declarative_base()
Session = sessionmaker()


H_LOGO = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
  <svg width="24px" height="28px" viewBox="0 0 24 28" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <rect fill="#ffffff" stroke="none" width="17.14407" height="16.046612" x="3.8855932" y="3.9449153" />
    <g id="Page-1" stroke="none" stroke-width="1" fill="none" fill-rule="evenodd">
        <path d="M0,2.00494659 C0,0.897645164 0.897026226,0 2.00494659,0 L21.9950534,0 C23.1023548,0 24,0.897026226 24,2.00494659 L24,21.9950534 C24,23.1023548 23.1029738,24 21.9950534,24 L2.00494659,24 C0.897645164,24 0,23.1029738 0,21.9950534 L0,2.00494659 Z M9,24 L12,28 L15,24 L9,24 Z M7.00811294,4 L4,4 L4,20 L7.00811294,20 L7.00811294,15.0028975 C7.00811294,12.004636 8.16824717,12.0097227 9,12 C10,12.0072451 11.0189302,12.0606714 11.0189302,14.003477 L11.0189302,20 L14.0270431,20 L14.0270431,13.1087862 C14.0270433,10 12,9.00309038 10,9.00309064 C8.01081726,9.00309091 8,9.00309086 7.00811294,11.0019317 L7.00811294,4 Z M19,19.9869002 C20.1045695,19.9869002 21,19.0944022 21,17.9934501 C21,16.892498 20.1045695,16 19,16 C17.8954305,16 17,16.892498 17,17.9934501 C17,19.0944022 17.8954305,19.9869002 19,19.9869002 Z" id="Rectangle-2-Copy-17" fill="currentColor"></path>
    </g>
</svg>"""


class Group(Base):
    __tablename__ = "group"

    id = sa.Column(sa.Integer, primary_key=True)
    pubid = sa.Column(sa.Text())
    authority = sa.Column(sa.UnicodeText())


class Organization(Base):
    __tablename__ = "organization"
    id = sa.Column(sa.Integer, primary_key=True)
    pubid = sa.Column(sa.Text, unique=True)
    name = sa.Column(sa.UnicodeText, index=True)
    logo = sa.Column(sa.UnicodeText)
    authority = sa.Column(sa.UnicodeText)


def upgrade():
    session = Session(bind=op.get_bind())

    default_org = (
        session.query(Organization).filter_by(pubid="__default__").one_or_none()
    )
    if default_org:
        log.info("__default__ organization already exists, not creating it")
        return

    log.info("__default__ organization doesn't exist yet, creating it")
    authority = session.query(Group).filter_by(pubid="__world__").one().authority
    session.add(
        Organization(
            name="Hypothesis", logo=H_LOGO, pubid="__default__", authority=authority
        )
    )
    session.commit()


def downgrade():
    # Don't try to delete the __default__ organization when downgrading
    # because there might be groups that are related to it.
    pass
