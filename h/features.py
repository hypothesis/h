# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pyramid.view import view_config
import sqlalchemy as sa

from h.db import Base

FEATURES = {
    'claim': "Enable 'claim your username' web views?",
    'show_unanchored_annotations': "Show annotations that fail to anchor?",
    'truncate_annotations': "Truncate long quotes and bodies in annotations?",
}


class UnknownFeatureError(Exception):
    pass


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
            feat = cls.get_by_name(name)
            if feat is None:
                feat = cls(name=name)
                cls.query.session.add(feat)
            results.append(feat)
        return results

    @classmethod
    def get_by_name(cls, name):
        """Fetch a flag by name."""
        return cls.query.filter(cls.name == name).first()


def flag_enabled(request, name):
    """
    Determine if the named feature is enabled for the current request.

    If the feature has no override in the database, it will default to False.
    Features must be documented, and an UnknownFeatureError will be thrown if
    an undocumented feature is interrogated.
    """
    if name not in FEATURES:
        raise UnknownFeatureError(
            '{0} is not a valid feature name'.format(name))

    feat = Feature.get_by_name(name)

    # Features that don't exist in the database are off.
    if feat is None:
        return False
    # Features that are on for everyone are on.
    if feat.everyone:
        return True
    # Features that are on for admin are on if the current user is an admin.
    if feat.admins and 'group:__admin__' in request.effective_principals:
        return True
    # Features that are on for staff are on if the current user is a staff
    # member.
    if feat.staff and 'group:__staff__' in request.effective_principals:
        return True
    return False


@view_config(route_name='features_status',
             request_method='GET',
             accept='application/json',
             renderer='json',
             http_cache=(0, {'no_store': False}))
def features_status(request):
    """Report current feature flag values."""
    return {k: flag_enabled(request, k) for k in FEATURES.keys()}


def includeme(config):
    config.add_request_method(flag_enabled, name='feature')

    config.add_route('features_status', '/app/features')

    config.scan(__name__)
