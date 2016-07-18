# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h import models
from h.api.search import index
from h.util.user import userid_from_username


class UserRenameError(Exception):
    pass


class RenameUserService(object):
    """
    Renames a user and updates all its annotations and when necessary the NIPSA
    status.

    ``check`` should be called first

    Validates the new username and updates the User. The permissions of
    the user's annotations are updated to reflect the new username.

    May raise a ValueError if the new username does not validate or
    UserRenameError if the new username is already taken by another account.
    """
    def __init__(self, request):
        self.request = request
        self.session = request.db

    def check(self, new_username):
        existing_user = models.User.get_by_username(self.session, new_username)
        if existing_user:
            raise UserRenameError('Another user already has the username "%s"' % new_username)

        return True

    def rename(self, user, new_username):
        self.check(new_username)

        old_username = user.username

        user.username = new_username
        ids = self._change_annotations(old_username, new_username)
        self.request.tm.commit()

        self._reindex_annotations(ids)

    def _change_annotations(self, old_username, new_username):
        new_userid = userid_from_username(new_username, self.request.auth_domain)
        annotations = self._fetch_annotations(old_username)

        ids = set()
        for annotation in annotations:
            annotation.userid = new_userid
            ids.add(annotation.id)

        return ids

    def _reindex_annotations(self, ids):
        if ids:
            indexer = index.BatchIndexer(self.request.db, self.request.es, self.request)
            indexer.index(ids)

    def _fetch_annotations(self, username):
        userid = userid_from_username(username, self.request.auth_domain)
        return self.session.query(models.Annotation).filter(
            models.Annotation.userid == userid).yield_per(100)


def rename_user_factory(context, request):
    """Return a RenameUserService instance for the passed context and request."""
    return RenameUserService(request)
