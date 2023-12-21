import sqlalchemy as sa

from h import pubid
from h.db import Base, mixins


class Organization(Base, mixins.Timestamps):
    DEFAULT_PUBID = "__default__"
    NAME_MIN_CHARS = 1
    NAME_MAX_CHARS = 25
    LOGO_MAX_CHARS = 100000

    __tablename__ = "organization"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    # We don't expose the integer PK to the world, so we generate a short
    # random string to use as the publicly visible ID.
    pubid = sa.Column(sa.Text(), default=pubid.generate, unique=True, nullable=False)

    name = sa.Column(sa.UnicodeText(), nullable=False, index=True)

    logo = sa.Column(sa.UnicodeText())

    authority = sa.Column(sa.UnicodeText(), nullable=False)

    @sa.orm.validates("name")
    def validate_name(self, _key, name):
        if not (
            Organization.NAME_MIN_CHARS <= len(name) <= Organization.NAME_MAX_CHARS
        ):
            raise ValueError(
                f"name must be between {Organization.NAME_MIN_CHARS} and {Organization.NAME_MAX_CHARS} characters long"
            )
        return name

    def __repr__(self):
        return f"<Organization: {self.pubid}>"

    @property
    def is_default(self):
        return self.pubid == self.DEFAULT_PUBID
