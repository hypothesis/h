# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from functools import partial

import sqlalchemy

from h import mailer
from h.emails import signup
from h.models import Activation, Annotation, Subscriptions, User
from h import util


class LoginError(Exception):
    pass


class UserNotActivated(LoginError):
    """Tried to log in to an unactivated user account."""


class UserNotKnown(LoginError):
    """User not found while attempting to log in."""


class UserService(object):

    """A service for retrieving and performing common operations on users."""

    def __init__(self, default_authority, session):
        """
        Create a new user service.

        :param default_authority: the default authority for users
        :param session: the SQLAlchemy session object
        """
        self.default_authority = default_authority
        self.session = session

        # Local cache of fetched users.
        self._cache = {}

        # But don't allow the cache to persist after the session is closed.
        @sqlalchemy.event.listens_for(session, 'after_commit')
        @sqlalchemy.event.listens_for(session, 'after_rollback')
        def flush_cache(session):
            self._cache = {}

    def fetch(self, userid_or_username, authority=None):
        """
        Fetch a user by userid or by username and authority.

        Takes *either* a userid *or* a username and authority as arguments.
        For example::

          user_service.fetch('acct:foo@example.com')

        or::

          user_service.fetch('foo', 'example.com')

        :returns: a user instance, if found
        :rtype: h.models.User or None

        """
        if authority is not None:
            username = userid_or_username
        else:
            userid = userid_or_username
            parts = util.user.split_user(userid)
            username = parts['username']
            authority = parts['domain']

        # The cache is keyed by (username, authority) tuples.
        cache_key = (username, authority)

        if cache_key not in self._cache:
            self._cache[cache_key] = (self.session.query(User)
                                      .filter_by(username=username)
                                      .filter_by(authority=authority)
                                      .one_or_none())

        return self._cache[cache_key]

    def login(self, username_or_email, password):
        """
        Attempt to login using *username_or_email* and *password*.

        :returns: A user object if login succeeded, None otherwise.
        :rtype: h.models.User or NoneType
        :raises UserNotActivated: When the user is not activated.
        :raises UserNotKnown: When the user cannot be found in the default
            authority.
        """
        filters = {'authority': self.default_authority}
        if '@' in username_or_email:
            filters['email'] = username_or_email
        else:
            filters['username'] = username_or_email

        user = (self.session.query(User)
                .filter_by(**filters)
                .one_or_none())

        if user is None:
            raise UserNotKnown()

        if not user.is_activated:
            raise UserNotActivated()

        if user.check_password(password):
            return user

        return None

    def annotation_count(self, userid):
        """
        Return the count of shared annotations for this user.
        """

        return (
            self.session.query(Annotation)
            .filter_by(userid=userid, groupid='__world__',  shared=True)
            .count())


class UserSignupService(object):

    """A service for registering users."""

    def __init__(self,
                 default_authority,
                 mailer,
                 session,
                 signup_email,
                 stats=None):
        """
        Create a new user signup service.

        :param default_authority: the default authority for new users
        :param mailer: a mailer (such as :py:mod:`h.mailer`)
        :param session: the SQLAlchemy session object
        :param signup_email: a function for generating a signup email
        :param stats: the stats service
        """
        self.default_authority = default_authority
        self.mailer = mailer
        self.session = session
        self.signup_email = signup_email
        self.stats = stats

    def signup(self, require_activation=True, **kwargs):
        """
        Create a new user.

        If *require_activation* is ``True``, the user will be flagged as
        requiring activation and an activation email will be sent.

        :param require_activation: The name to use.
        :type require_activation: bool.

        Remaining keyword arguments are passed to the
        :py:class:`h.models.User` constructor.

        :returns: the newly-created user object.
        :rtype: h.models.User
        """
        kwargs.setdefault('authority', self.default_authority)
        user = User(**kwargs)
        self.session.add(user)

        # Create a new activation for the user
        if require_activation:
            self._require_activation(user)

        # FIXME: this is horrible, but is needed until the
        # notification/subscription system is made opt-out rather than opt-in
        # (at least from the perspective of the database).
        sub = Subscriptions(uri=user.userid, type='reply', active=True)
        self.session.add(sub)

        # Record a registration with the stats service
        if self.stats is not None:
            self.stats.incr('auth.local.register')

        return user

    def _require_activation(self, user):
        activation = Activation()
        self.session.add(activation)
        user.activation = activation

        # Flush the session to ensure that the user can be created and the
        # activation is successfully wired up.
        self.session.flush()

        # Send the activation email
        mail_params = self.signup_email(id=user.id,
                                        email=user.email,
                                        activation_code=user.activation.code)
        self.mailer.send.delay(*mail_params)


def user_service_factory(context, request):
    """Return a UserService instance for the passed context and request."""
    return UserService(default_authority=request.auth_domain,
                       session=request.db)


def user_signup_service_factory(context, request):
    """Return a UserSignupService instance for the passed context and request."""
    return UserSignupService(default_authority=request.auth_domain,
                             mailer=mailer,
                             session=request.db,
                             signup_email=partial(signup.generate, request),
                             stats=request.stats)
