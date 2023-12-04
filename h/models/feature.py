import logging

import sqlalchemy as sa

from h.db import Base

log = logging.getLogger(__name__)

FEATURES = {
    "embed_cachebuster": (
        "Cache-bust client entry point URL to prevent browser/CDN from "
        "using a cached version?"
    ),
    "client_display_names": "Render display names instead of user names in the client",
    "html_side_by_side": "Enable side-by-side mode for web pages in the client",
    "pdf_custom_text_layer": "Use custom text layer in PDFs for improved text selection",
    "styled_highlight_clusters": "Style different clusters of highlights in the client",
    "client_user_profile": "Enable client-side user profile and preferences management",
    "export_annotations": "Allow users to export annotations",
    "import_annotations": "Allow users to import previously exported annotations",
    "export_formats": "Allow users to select the format for their annotations export file",
    "page_numbers": "Display page numbers on annotations, if available",
    "search_panel": "Use a sidebar panel to display search form",
}

# Once a feature has been fully deployed, we remove the flag from the codebase.
# We can't do this in one step, because removing it entirely will cause stage
# to remove the flag data from the database on boot, which will in turn disable
# the feature in prod.
#
# Instead, the procedure for removing a feature is as follows:
#
# 1. Remove all feature lookups for the named feature throughout the code.
#
# 2. Move the feature to FEATURES_PENDING_REMOVAL. This ensures that the
#    feature won't show up in the admin panel, and any uses of the feature will
#    provoke UnknownFeatureErrors (server-side) or console warnings
#    (client-side).
#
# 3. Deploy these changes all the way out to production.
#
# 4. Finally, remove the feature from FEATURES_PENDING_REMOVAL.
#
FEATURES_PENDING_REMOVAL = {}


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
        # N.B. We remove only those features we know absolutely nothing about,
        # which means that FEATURES_PENDING_REMOVAL are left alone.
        known = set(FEATURES) | set(FEATURES_PENDING_REMOVAL)
        unknown_flags = session.query(cls).filter(sa.not_(cls.name.in_(known)))
        count = unknown_flags.delete(synchronize_session=False)
        if count > 0:  # pragma: no cover
            log.info("removed %d old/unknown feature flags from database", count)

    def __repr__(self):  # pragma: no cover
        return "<Feature {f.name} everyone={f.everyone}>".format(f=self)
