import sqlalchemy as sa

from h.db import Base


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
        # pylint: disable=consider-using-f-string
        return "{}(provider={!r}, provider_unique_id={!r})".format(
            self.__class__.__name__, self.provider, self.provider_unique_id
        )
