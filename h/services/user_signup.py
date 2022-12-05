import logging

from pyramid.request import Request
from sqlalchemy.exc import IntegrityError

from h.emails import signup
from h.models import Activation, User, UserIdentity
from h.services import SubscriptionService
from h.services.exceptions import ConflictError
from h.services.user_password import UserPasswordService
from h.tasks import mailer as tasks_mailer

log = logging.getLogger(__name__)


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

    def signup(self, require_activation: bool = True, **kwargs) -> User:
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
        user.identities = [UserIdentity(user=user, **i_args) for i_args in identities]

        self.session.add(user)

        if password is not None:
            self.password_service.update_password(user, password)

        # Create a new activation for the user
        if require_activation:
            try:
                self._require_activation(user)
            except IntegrityError as err:
                # When identical signup requests get issued at nearly the same time, they
                # race each other to the database and result in unique contraint integrity
                # errors on the user's email or username within the authority.
                if (
                    'duplicate key value violates unique constraint "uq__user__email"'
                    in err.args[0]
                    or 'duplicate key value violates unique constraint "ix__user__userid"'
                    in err.args[0]
                ):
                    log.warning(
                        "concurrent account signup conflict error occurred during user signup %s",
                        err.args[0],
                    )
                    raise ConflictError(
                        f"The email address {user.email} has already been registered."
                    ) from err
                # If the exception is not related to the email or username, re-raise it.
                raise

        # FIXME: this is horrible, but is needed until the
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
        mail_params = signup.generate(
            request=self.request,
            user_id=user.id,
            email=user.email,
            activation_code=user.activation.code,
        )
        tasks_mailer.send.delay(*mail_params)


def user_signup_service_factory(_context, request):
    """Return a UserSignupService instance for the passed context and request."""

    return UserSignupService(
        request=request,
        default_authority=request.default_authority,
        password_service=request.find_service(name="user_password"),
        subscription_service=request.find_service(SubscriptionService),
    )
