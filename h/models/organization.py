# -*- coding: utf-8 -*-

import sqlalchemy as sa
from xml.etree import ElementTree

from h.db import Base
from h.db import mixins
from h import pubid

ORGANIZATION_NAME_MIN_CHARS = 1
ORGANIZATION_NAME_MAX_CHARS = 25
ORGANIZATION_LOGO_MAX_CHARS = 10000


class Organization(Base, mixins.Timestamps):
    __tablename__ = 'organization'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    # We don't expose the integer PK to the world, so we generate a short
    # random string to use as the publicly visible ID.
    pubid = sa.Column(sa.Text(),
                      default=pubid.generate,
                      unique=True,
                      nullable=False)

    name = sa.Column(sa.UnicodeText(), nullable=False, index=True)

    logo = sa.Column(sa.UnicodeText())

    authority = sa.Column(sa.UnicodeText(), nullable=False)

    @sa.orm.validates('name')
    def validate_name(self, key, name):
        if not (ORGANIZATION_NAME_MIN_CHARS <= len(name) <= ORGANIZATION_NAME_MAX_CHARS):
            raise ValueError(
                'name must be between {min} and {max} characters long'
                .format(min=ORGANIZATION_NAME_MIN_CHARS,
                        max=ORGANIZATION_NAME_MAX_CHARS))
        return name

    @sa.orm.validates('logo')
    def validate_logo(self, key, logo):
        if not (len(logo) <= ORGANIZATION_LOGO_MAX_CHARS):
            raise ValueError(
                'logo must be less than {max} characters long'
                .format(max=ORGANIZATION_NAME_MAX_CHARS))
        try:
            root = ElementTree.fromstring(logo)
        except ElementTree.ParseError:
            raise ValueError('logo is not a valid SVG (could not parse XML)')
        if root.tag != 'svg':
            raise ValueError('logo is not a valid SVG (does not start with an <svg> tag')
        return logo

    def __repr__(self):
        return '<Organization: %s>' % self.pubid
