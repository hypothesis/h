# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from sqlalchemy.exc import SQLAlchemyError

from h.services.exceptions import ValidationError, ConflictError


class GroupUpdateService(object):
    def __init__(self, session):
        """
        Create a new GroupUpdateService

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

        :rtype: ~h.models.Group
        """

        for key, value in kwargs.items():
            try:
                setattr(group, key, value)
            except ValueError as err:
                raise ValidationError(err)

        try:
            self.session.flush()

        except SQLAlchemyError as err:
            # Handle DB integrity issues with duplicate ``authority_provided_id``
            if (
                'duplicate key value violates unique constraint "ix__group__groupid"'
                in repr(err)
            ):
                raise ConflictError(
                    "authority_provided_id '{id}' is already in use".format(
                        id=kwargs["authority_provided_id"]
                    )
                )
            else:
                # Re-raise as this is an unexpected problem
                raise

        return group


def group_update_factory(context, request):
    """Return a GroupUpdateService instance for the passed context and request."""
    return GroupUpdateService(session=request.db)
