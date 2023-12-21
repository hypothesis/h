from h import models
from h.i18n import TranslationString as _


class DuplicateUserError(Exception):
    """Indicates that data violates user uniqueness constraints."""


class UserUniqueService:
    """A service for ensuring that data represents a unique user and will not constitute a duplicate user."""

    def __init__(self, session, user_service):
        """
        Create a new user_unique service.

        :param _session: the SQLAlchemy session object
        """
        self._session = session
        self.user_service = user_service

    def ensure_unique(self, data, authority):
        """
        Ensure the provided `data` would constitute a new, non-duplicate user.

        Check for conflicts in email, username, identity.

        :param data: dictionary of new-user data. Will check `email`, `username`
                     and any `identities` dictionaries provided
        :raises DuplicateUserError: if the data violate any uniqueness constraints

        :param authority: Authority against which to do a duplicate check
        """
        # pylint:disable=consider-using-f-string
        errors = []

        # check for duplicate email address
        if data.get("email", None) and (
            models.User.get_by_email(self._session, data["email"], authority)
            is not None
        ):
            errors.append(
                _("user with email address '{}' already exists".format(data["email"]))
            )

        # check for duplicate username
        if data.get("username", None) and (
            models.User.get_by_username(self._session, data["username"], authority)
            is not None
        ):
            errors.append(
                _("user with username '{}' already exists".format(data["username"]))
            )

        # check for duplicate identities
        # (provider, provider_unique_id) combinations
        identities = data.get("identities", [])
        for identity in identities:
            if self.user_service.fetch_by_identity(
                identity["provider"], identity["provider_unique_id"]
            ):
                errors.append(
                    _(
                        "user with provider '{}' and unique id '{}' already exists".format(
                            identity["provider"], identity["provider_unique_id"]
                        )
                    )
                )

        if errors:
            raise DuplicateUserError(", ".join(errors))


def user_unique_factory(_context, request):
    user_service = request.find_service(name="user")
    return UserUniqueService(session=request.db, user_service=user_service)
