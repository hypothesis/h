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
    user_id = sa.Column(
        sa.Integer(), sa.ForeignKey("user.id", ondelete="cascade"), nullable=False
    )

    def __repr__(self):
        return f"{self.__class__.__name__}(provider={self.provider!r}, provider_unique_id={self.provider_unique_id!r})"
