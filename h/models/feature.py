import logging

import sqlalchemy as sa

from h.db import Base

log = logging.getLogger(__name__)

FEATURES = {
    "client_display_names": "Render display names instead of user names in the client",
    "client_user_profile": "Enable client-side user profile and preferences management",
    "embed_cachebuster": (
        "Cache-bust client entry point URL to prevent browser/CDN from "
        "using a cached version?"
    ),
    "group_members": "Allow users to manage group members in new group forms",
    "group_type": "Allow users to choose group type in new group forms",
    "pdf_custom_text_layer": "Use custom text layer in PDFs for improved text selection",
    "styled_highlight_clusters": "Style different clusters of highlights in the client",
}


class Feature(Base):
    """A feature flag for the application."""

    __tablename__ = "feature"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.Text(), nullable=False, unique=True)

    # Is the feature enabled for everyone?
    everyone = sa.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.sql.expression.false(),
    )

    # Is the feature enabled for first-party users?
    first_party = sa.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.sql.expression.false(),
    )

    # Is the feature enabled for admins?
    admins = sa.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.sql.expression.false(),
    )

    # Is the feature enabled for all staff?
    staff = sa.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.sql.expression.false(),
    )

    @property
    def description(self):
        return FEATURES[self.name]

    @classmethod
    def all(cls, session):
        """Fetch (or, if necessary, create) rows for all defined features."""
        features = {f.name: f for f in session.query(cls) if f.name in FEATURES}

        # Add missing features
        missing = [cls(name=n) for n in FEATURES if n not in features]
        session.add_all(missing)

        return list(features.values()) + missing

    @classmethod
    def remove_old_flags(cls, session):
        """
        Remove old/unknown data from the feature table.

        When a feature flag is removed from the codebase, it will remain in the
        database. This could potentially cause very surprising issues in the
        event that a feature flag with the same name (but a different meaning)
        is added at some point in the future.

        This function removes unknown feature flags from the database.
        """
        known = set(FEATURES)
        unknown_flags = session.query(cls).filter(sa.not_(cls.name.in_(known)))
        count = unknown_flags.delete(synchronize_session=False)
        if count > 0:  # pragma: no cover
            log.info("removed %d old/unknown feature flags from database", count)

    def __repr__(self):  # pragma: no cover
        return "<Feature {f.name} everyone={f.everyone}>".format(f=self)
