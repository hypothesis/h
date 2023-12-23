from sqlalchemy.exc import SQLAlchemyError

from h.services.exceptions import ConflictError, ValidationError


class GroupUpdateService:
    def __init__(self, session):
        """
        Create a new GroupUpdateService.

        :param session: the SQLAlchemy session object
        """
        self.session = session

    def update(self, group, **kwargs):
        """
        Update a group model with the args provided.

        :arg group: the group to update
        :type group: ~h.models.Group

        :raise ValidationError: if setting an attribute on the model raises :exc:`ValueError`
        :raise ConflictError: if the ``authority_provided_id`` is already in use
        :raise SQLAlchemyError: if SQLAlchemy raises an unexpected SQLAlchemyError

        :rtype: ~h.models.Group
        """

        for key, value in kwargs.items():
            try:
                setattr(group, key, value)
            except ValueError as err:
                raise ValidationError(err) from err

        try:
            self.session.flush()

        except SQLAlchemyError as err:
            # Handle DB integrity issues with duplicate ``authority_provided_id``
            if (
                'duplicate key value violates unique constraint "ix__group__groupid"'
                in repr(err)
            ):
                raise ConflictError(
                    f"""authority_provided_id '{kwargs["authority_provided_id"]}' is already in use"""
                ) from err

            # Re-raise as this is an unexpected problem
            raise

        return group


def group_update_factory(_context, request):
    """Return a GroupUpdateService instance for the passed context and request."""
    return GroupUpdateService(session=request.db)
