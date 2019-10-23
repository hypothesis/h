"""
Move all groups to organizations.

We want every group to have a non-null organization with the same authority as
the group, so that we can make group.organization not-nullable.

This migration goes over all the groups in the database and:

1. Does nothing if the group already has an organization, or

2. Assigns the group to the `__default__` organization if the group has the
   same authority as the default organization (this migration assumes that a
   `__default__` organization exists in the database and will crash if not), or

3. Assigns the group to an organization in the group's authority, creating that
   organization if necessary.

For (3) this migration will create new organizations as necessary with the
organization's authority the same as the group's, the organization's name the
same string as the authority string, and a null organization logo.

This isn't what you'd want for an organization name and logo, but it will do
for this migration (it will do for ensuring that every group has a
same-authority organization so that we can make group.organization
non-nullable) and we can fix up the resulting organization names and logos
later.

"""
import logging
import random

import sqlalchemy as sa
from alembic import op
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

revision = "615358b6c428"
down_revision = "8a7f31c4525d"


log = logging.getLogger(__name__)


Base = declarative_base()
Session = sessionmaker()


def generate():
    """
    Return a random 8-character unicode string.

    This is the generate() function from h/pubid.py.

    """
    ALPHABET = "123456789ABDEGJKLMNPQRVWXYZabdegijkmnopqrvwxyz"
    return "".join(random.SystemRandom().choice(ALPHABET) for _ in range(8))


class Group(Base):
    __tablename__ = "group"
    id = sa.Column(sa.Integer, primary_key=True)
    authority = sa.Column(sa.UnicodeText, nullable=False)
    organization_id = sa.Column(sa.Integer, sa.ForeignKey("organization.id"))
    organization = sa.orm.relationship("Organization")


class Organization(Base):
    __tablename__ = "organization"
    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    created = sa.Column(sa.DateTime, server_default=sa.func.now(), nullable=False)
    updated = sa.Column(sa.DateTime, server_default=sa.func.now(), nullable=False)
    pubid = sa.Column(sa.Text, default=generate, unique=True, nullable=False)
    name = sa.Column(sa.UnicodeText, nullable=False, index=True)
    logo = sa.Column(sa.UnicodeText)
    authority = sa.Column(sa.UnicodeText, nullable=False)


def new_org(authority, session):
    organization = Organization(authority=authority, name=authority)
    session.add(organization)
    log.info("Created new organization {name}".format(name=organization.name))
    return organization


def get_org(authority, session):
    q = session.query(Organization)
    q = q.filter_by(authority=authority, name=authority)
    return q.one_or_none()


def get_or_create_org(authority, session):
    return get_org(authority, session) or new_org(authority, session)


def get_default_org(session):
    return session.query(Organization).filter_by(pubid="__default__").one()


def upgrade():
    session = Session(bind=op.get_bind())
    default_org = get_default_org(session)

    skipped = 0
    assigned_to_default_org = 0
    assigned_to_authority_org = 0

    for group in session.query(Group):
        if group.organization:
            skipped += 1

        elif group.authority == default_org.authority:
            group.organization = default_org
            assigned_to_default_org += 1

        else:
            group.organization = get_or_create_org(group.authority, session)
            assigned_to_authority_org += 1

    session.commit()

    log.info("Skipped {n} groups that already had an organization".format(n=skipped))
    log.info(
        "Assigned {n} groups to the __default__ organization".format(
            n=assigned_to_default_org
        )
    )
    log.info(
        "Assigned {n} groups to authority organizations".format(
            n=assigned_to_authority_org
        )
    )


def downgrade():
    pass
