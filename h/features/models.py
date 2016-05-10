# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import slugify

import sqlalchemy as sa
from sqlalchemy.orm import exc

from h.db import Base
from h.db import mixins

log = logging.getLogger(__name__)

FEATURES = {
    'direct_linking': "Generate direct links to annotations in context in the client?",
    'new_homepage': "Show the new homepage design?",
    'postgres': 'Read/write annotation and document data from/to postgres'
}

COHORT_NAME_MIN_LENGTH = 4
COHORT_NAME_MAX_LENGTH = 25


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
FEATURES_PENDING_REMOVAL = {
    'claim': "Enable 'claim your username' web views?",
    'ops_disable_streamer_uri_equivalence': "[Ops] Disable streamer URI equivalence support?",
}


class Feature(Base):

    """A feature flag for the application."""

    __tablename__ = 'feature'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.Text(), nullable=False, unique=True)

    # Is the feature enabled for everyone?
    everyone = sa.Column(sa.Boolean,
                         nullable=False,
                         default=False,
                         server_default=sa.sql.expression.false())

    # Is the feature enabled for admins?
    admins = sa.Column(sa.Boolean,
                       nullable=False,
                       default=False,
                       server_default=sa.sql.expression.false())

    # Is the feature enabled for all staff?
    staff = sa.Column(sa.Boolean,
                      nullable=False,
                      default=False,
                      server_default=sa.sql.expression.false())

    @property
    def description(self):
        return FEATURES[self.name]

    @classmethod
    def all(cls):
        """Fetch (or, if necessary, create) rows for all defined features."""
        results = []
        for name in FEATURES:
            feat = cls.query.filter(cls.name == name).first()
            if feat is None:
                feat = cls(name=name)
                cls.query.session.add(feat)
            results.append(feat)
        return results

    @classmethod
    def remove_old_flags(cls):
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
        unknown_flags = cls.query.filter(sa.not_(cls.name.in_(known)))
        count = unknown_flags.delete(synchronize_session=False)
        if count > 0:
            log.info('removed %d old/unknown feature flags from database', count)

    def __repr__(self):
        return '<Feature {f.name} everyone={f.everyone}>'.format(f=self)


class Cohort(Base, mixins.Timestamps):
    __tablename__ = 'cohort'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.UnicodeText(), nullable=False, index=True)

    # Cohort membership
    members = sa.orm.relationship(
        'User', secondary='user_cohort', backref=sa.orm.backref(
            'cohorts', order_by='Cohort.name'))

    def __init__(self, name, creator):
        self.name = name
        self.creator = creator
        self.members.append(creator)

    @sa.orm.validates('name')
    def validate_name(self, key, name):
        if not COHORT_NAME_MIN_LENGTH <= len(name) <= COHORT_NAME_MAX_LENGTH:
            raise ValueError('name must be between {min} and {max} characters '
                             'long'.format(min=COHORT_NAME_MIN_LENGTH,
                                           max=COHORT_NAME_MAX_LENGTH))
        return name

    def __repr__(self):
        return '<Cohort: %s>' % self.slug

    @property
    def slug(self):
        """A version of this group's name suitable for use in a URL."""
        return slugify.slugify(self.name)

    @classmethod
    def get_by_id(cls, id_):
        """Return the cohort with the given id, or None."""
        try:
            return cls.query.filter(cls.id == id_).one()
        except exc.NoResultFound:
            return None


USER_COHORT_TABLE = sa.Table(
    'user_cohort', Base.metadata,
    sa.Column('user_id',
              sa.Integer,
              sa.ForeignKey('user.id'),
              nullable=False),
    sa.Column('cohort_id',
              sa.Integer,
              sa.ForeignKey('cohort.id'),
              nullable=False)
)
