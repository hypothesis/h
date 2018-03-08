import sqlalchemy as sa
import slugify
from xml.etree import ElementTree

from h.db import Base
from h.db import mixins


ORGANIZATION_NAME_MIN_CHARS = 1
ORGANIZATION_NAME_MAX_CHARS = 25
ORGANIZATION_LOGO_MAX_CHARS = 10000


class Organization(Base, mixins.Timestamps):
    __tablename__ = 'organization'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    name = sa.Column(sa.UnicodeText(), nullable=False, index=True)

    logo = sa.Column(sa.UnicodeText())

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
        return '<Organization: %s>' % self.slug
