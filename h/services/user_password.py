# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

from h._compat import text_type
from h.security import password_context

# FIXME: This service currently interacts with the underscored "_password"
# property of the user model. This is to make it possible to roll this change
# out incrementally. When all password checking functionality has been removed
# from the user model, we should rename the password hash property to plain
# "password" (no underscore) and use that in this service.


class UserPasswordService(object):

    """
    A service for checking and updating user passwords.

    This service is responsible for verifying and updating user passwords, and
    specifically for ensuring that we automatically upgrade user password
    hashes to the latest secure hash when verifying, if appropriate.
    """

    def __init__(self):
        # Test seam
        self.hasher = password_context

    def check_password(self, user, password):
        """Check the password for this user, and upgrade it if necessary."""
        if not user._password:
            return False

        # Old-style separate salt.
        #
        # TODO: remove this deprecated code path when a suitable proportion of
        # users have updated their password by logging-in. (Check how many
        # users still have a non-null salt in the database.)
        if user.salt is not None:
            verified = self.hasher.verify(password + user.salt, user._password)

            # If the password is correct, take this opportunity to upgrade the
            # password and remove the salt.
            if verified:
                self.update_password(user, password)

            return verified

        verified, new_hash = self.hasher.verify_and_update(password,
                                                           user._password)
        if not verified:
            return False

        if new_hash is not None:
            user._password = text_type(new_hash)

        return verified

    def update_password(self, user, new_password):
        """Update the user's password."""
        # Remove any existing explicit salt (the password context salts the
        # password automatically).
        user.salt = None
        user._password = text_type(self.hasher.encrypt(new_password))
        user.password_updated = datetime.datetime.utcnow()


def user_password_service_factory(context, request):
    """Return a UserPasswordService instance for the passed context and request."""
    return UserPasswordService()
