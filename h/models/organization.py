# -*- coding: utf-8 -*-

import sqlalchemy as sa
import slugify

from h.db import Base
from h.db import mixins
from h import pubid

ORGANIZATION_NAME_MIN_CHARS = 1
ORGANIZATION_NAME_MAX_CHARS = 25


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

    @property
    def slug(self):
        """A version of this organization's name suitable for use in a URL."""
        return slugify.slugify(self.name)

    @sa.orm.validates('name')
    def validate_name(self, key, name):
        if not (ORGANIZATION_NAME_MIN_CHARS <= len(name) <= ORGANIZATION_NAME_MAX_CHARS):
            raise ValueError(
                'name must be between {min} and {max} characters long'
                .format(min=ORGANIZATION_NAME_MIN_CHARS,
                        max=ORGANIZATION_NAME_MAX_CHARS))
        return name

    def __repr__(self):
        return '<Organization: %s>' % self.slug
