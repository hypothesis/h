from sqlalchemy.exc import SQLAlchemyError

from h.services.exceptions import ConflictError, ValidationError


class UserUpdateService:
    def __init__(self, session):
        """
        Create a new UserUpdateService.

        :param session: the SQLAlchemy session object
        """
        self.session = session

    def update(self, user, **kwargs):
        """
        Update a user model with the args provided.

        :arg user: the group to update
        :type user: ~h.models.User

        :raise ValidationError: if setting an attribute on the model raises :exc:`ValueError`
                                or if ``authority`` is present in ``kwargs``
        :raise ConflictError: if the new username is already in use
        :raise SQLAlchemyError: if SQLAlchemy raises an unexpected SQLAlchemyError

        :rtype: ~h.models.User
        """

        # Much repurcussion if a user's authority is changed at this point.
        # May wish to re-evaluate later if users need to be moved between
        # authorities.
        if "authority" in kwargs:
            raise ValidationError("A user's authority may not be changed")

        for key, value in kwargs.items():
            try:
                setattr(user, key, value)
            except ValueError as err:
                raise ValidationError(err) from err

        try:
            self.session.flush()

        except SQLAlchemyError as err:
            # Handle DB integrity issues with duplicate ``authority_provided_id``
            if (
                'duplicate key value violates unique constraint "ix__user__userid"'
                in repr(err)
            ):
                # This conflict can arise from changes to either username or authority.
                # We know this isn't authority, because the presence of authority
                # would have already raised.
                raise ConflictError(
                    f"""username '{kwargs["username"]}' is already in use"""
                ) from err

            # Re-raise as this is an unexpected problem
            raise

        return user


def user_update_factory(_context, request):
    """Return a UserUpdateService instance for the passed context and request."""
    return UserUpdateService(session=request.db)
