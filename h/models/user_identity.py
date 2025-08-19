from enum import StrEnum

import sqlalchemy as sa

from h.db import Base


class IdentityProvider(StrEnum):
    ORCID = "orcid.org"
    GOOGLE = "google.com"
    FACEBOOK = "facebook.com"


class UserIdentity(Base):
    __tablename__ = "user_identity"
    __table_args__ = (sa.UniqueConstraint("provider", "provider_unique_id"),)

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)
    provider = sa.Column(sa.UnicodeText(), nullable=False)
    provider_unique_id = sa.Column(sa.UnicodeText(), nullable=False)

    email = sa.Column(sa.UnicodeText())

    name = sa.Column(sa.UnicodeText())
    given_name = sa.Column(sa.UnicodeText())
    family_name = sa.Column(sa.UnicodeText())

    user_id = sa.Column(
        sa.Integer(), sa.ForeignKey("user.id", ondelete="cascade"), nullable=False
    )

    @property
    def display_name(self) -> sa.Column[str] | str | None:
        if self.name:
            return self.name

        if self.given_name and self.family_name:
            return f"{self.given_name} {self.family_name}"

        if self.given_name:
            return self.given_name

        return None

    def __repr__(self):
        return f"{self.__class__.__name__}(provider={self.provider!r}, provider_unique_id={self.provider_unique_id!r})"
