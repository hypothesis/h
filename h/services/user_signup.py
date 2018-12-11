# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from functools import partial

from h.emails import signup
from h.models import Activation, Subscriptions, User, UserIdentity
from h.tasks import mailer


class UserSignupService(object):

    """A service for registering users."""

    def __init__(
        self,
        default_authority,
        mailer,
        session,
        signup_email,
        password_service,
        stats=None,
    ):
        """
        Create a new user signup service.

        :param default_authority: the default authority for new users
        :param mailer: a mailer (such as :py:mod:`h.tasks.mailer`)
        :param session: the SQLAlchemy session object
        :param signup_email: a function for generating a signup email
        :param password_service: the user password service
        :param stats: the stats service
        """
        self.default_authority = default_authority
        self.mailer = mailer
        self.session = session
        self.signup_email = signup_email
        self.password_service = password_service
        self.stats = stats

    def signup(self, require_activation=True, **kwargs):
        """
        Create a new user.

        If *require_activation* is ``True``, the user will be flagged as
        requiring activation and an activation email will be sent.

        :param require_activation: The name to use.
        :type require_activation: bool.

        :param identities: A list of dictionaries representing identities to
          add to the new user. Each dictionary will be passed as keyword args
          to :py:class:`h.models.UserIdentity`.

        Remaining keyword arguments are used to construct a new
        :py:class:`h.models.User` object.

        :returns: the newly-created user object.
        :rtype: h.models.User
        """
        kwargs.setdefault("authority", self.default_authority)

        # We extract any passed password as we use that separately to set the
        # user's password.
        password = kwargs.pop("password", None)

        # Extract any passed identities for this new user
        identities = kwargs.pop("identities", [])

        user = User(**kwargs)

        # Add identity relations to this new user, if provided
        user.identities = [UserIdentity(user=user, **i_args) for i_args in identities]

        self.session.add(user)

        if password is not None:
            self.password_service.update_password(user, password)

        # Create a new activation for the user
        if require_activation:
            self._require_activation(user)

        # FIXME: this is horrible, but is needed until the
        # notification/subscription system is made opt-out rather than opt-in
        # (at least from the perspective of the database).
        sub = Subscriptions(uri=user.userid, type="reply", active=True)
        self.session.add(sub)

        # Record a registration with the stats service
        if self.stats is not None:
            self.stats.incr("auth.local.register")

        return user

    def _require_activation(self, user):
        activation = Activation()
        self.session.add(activation)
        user.activation = activation

        # Flush the session to ensure that the user can be created and the
        # activation is successfully wired up.
        self.session.flush()

        # Send the activation email
        mail_params = self.signup_email(
            id=user.id, email=user.email, activation_code=user.activation.code
        )
        self.mailer.send.delay(*mail_params)


def user_signup_service_factory(context, request):
    """Return a UserSignupService instance for the passed context and request."""
    return UserSignupService(
        default_authority=request.default_authority,
        mailer=mailer,
        session=request.db,
        signup_email=partial(signup.generate, request),
        password_service=request.find_service(name="user_password"),
        stats=request.stats,
    )
