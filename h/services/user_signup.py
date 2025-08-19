import logging
from dataclasses import asdict

from psycopg2.errors import UniqueViolation
from pyramid.request import Request
from sqlalchemy.exc import IntegrityError

from h.emails import signup
from h.models import Activation, User, UserIdentity
from h.services import SubscriptionService
from h.services.email import EmailTag, TaskData
from h.services.user_password import UserPasswordService
from h.tasks import email

log = logging.getLogger(__name__)


class UsernameConflictError(Exception):
    """Signup failed because the username is already taken."""


class EmailConflictError(Exception):
    """Signup failed because the email address is already taken."""


class IdentityConflictError(Exception):
    """Signup failed because the identity is already taken."""


class UserSignupService:
    """A service for registering users."""

    def __init__(
        self,
        request: Request,
        default_authority: str,
        password_service: UserPasswordService,
        subscription_service: SubscriptionService,
    ):
        """
        Create a new user signup service.

        :param request: Pyramid request object
        :param default_authority: Default authority for new users
        :param password_service: User password service
        :param subscription_service: Service for creating subscriptions
        """
        self.request = request
        self.session = request.db
        self.default_authority = default_authority
        self.password_service = password_service
        self.subscription_service = subscription_service

    def signup(self, require_activation: bool = True, **kwargs) -> User:  # noqa: FBT001, FBT002
        """
        Create a new user.

        If `require_activation` is `True`, the user will be flagged as
        requiring activation and an activation email will be sent.

        Remaining keyword arguments are used to construct a new
        `h.models.User` object.

            * `identities` - A list of dictionaries representing identities to
              add to the new user. Each dictionary will be passed as keyword
              args to `h.models.UserIdentity`.

        :param require_activation: The name to use.
        """
        kwargs.setdefault("authority", self.default_authority)

        # We extract any passed password as we use that separately to set the
        # user's password.
        password = kwargs.pop("password", None)

        # Extract any passed identities for this new user
        identities = kwargs.pop("identities", [])

        user = User(**kwargs)

        # Add identity relations to this new user, if provided
        user.identities = [
            UserIdentity(
                user=user,
                provider=i_args["provider"],
                provider_unique_id=str(i_args["provider_unique_id"]),
                email=i_args.get("email"),
                name=i_args.get("name"),
                given_name=i_args.get("given_name"),
                family_name=i_args.get("family_name"),
            )
            for i_args in identities
        ]

        self.session.add(user)
        try:
            self.session.flush()
        except IntegrityError as err:
            # Concurrent, conflicting signup requests can all pass validation
            # (each request finding that no matching user exists in the DB)
            # and go on to try to insert conflicting users. When this happens
            # one of the requests successfully inserts a user and the others
            # fail here with an IntegrityError.
            #
            # Raise different exceptions depending on which column was in
            # conflict because this is of interest to exception handlers in the
            # calling code.
            #
            # But note that if this code raises an exception about one column
            # being in conflict that doesn't mean that other columns were not
            # *also* in conflict: two requests can try to insert users with the
            # same email address, username *and* identity.
            #
            # As soon as the first integrity check fails Postgres raises an
            # error. It doesn't continue to process other constraints to see
            # what other checks would have also failed.
            if (
                isinstance(err.orig, UniqueViolation)
                and err.orig.diag.constraint_name == "uq__user__email"
            ):
                raise EmailConflictError from err

            if (
                isinstance(err.orig, UniqueViolation)
                and err.orig.diag.constraint_name == "ix__user__userid"
            ):
                raise UsernameConflictError from err

            if (
                isinstance(err.orig, UniqueViolation)
                and err.orig.diag.constraint_name == "uq__user_identity__provider"
            ):
                raise IdentityConflictError from err

            # We should never get here: AFAIK no other types of IntegrityError
            # are possible here.
            # This `raise` is just here so that if an unexpected IntegrityError
            # somehow does happen we don't silence it.
            raise  # pragma: no cover

        if password is not None:
            self.password_service.update_password(user, password)

        # Create a new activation for the user
        if require_activation:
            self._require_activation(user)

        # FIXME: this is horrible, but is needed until the  # noqa: FIX001, TD001, TD002, TD003
        # notification/subscription system is made opt-out rather than opt-in
        # (at least from the perspective of the database).
        for subscription in self.subscription_service.get_all_subscriptions(
            user_id=user.userid
        ):
            subscription.active = True

        return user

    def _require_activation(self, user):
        activation = Activation()
        self.session.add(activation)
        user.activation = activation

        # Flush the session to ensure that the user can be created and the
        # activation is successfully wired up.
        self.session.flush()

        # Send the activation email
        email_data = signup.generate(
            request=self.request,
            user_id=user.id,
            email=user.email,
            activation_code=user.activation.code,
        )
        task_data = TaskData(
            tag=EmailTag.ACTIVATION, sender_id=user.id, recipient_ids=[user.id]
        )
        email.send.delay(asdict(email_data), asdict(task_data))


def user_signup_service_factory(_context, request):
    """Return a UserSignupService instance for the passed context and request."""

    return UserSignupService(
        request=request,
        default_authority=request.default_authority,
        password_service=request.find_service(name="user_password"),
        subscription_service=request.find_service(SubscriptionService),
    )
