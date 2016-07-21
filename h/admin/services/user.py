# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h import models
from h.api.search import index
from h.util.user import userid_from_username


class UserRenameError(Exception):
    pass


class RenameUserService(object):
    """
    Renames a user and updates all its annotations.

    ``check`` should be called first

    Validates the new username and updates the User. The user's annotations
    userid field will be updated. It accepts a reindex function that gets a
    list of annotation ids, it is then the function's responsibility to reindex
    these annotations in the search index.

    May raise a ValueError if the new username does not validate or
    UserRenameError if the new username is already taken by another account.
    """
    def __init__(self, session, auth_domain, reindex):
        self.session = session
        self.auth_domain = auth_domain
        self.reindex = reindex

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

        self.reindex(ids)

    def _change_annotations(self, old_username, new_username):
        new_userid = userid_from_username(new_username, self.auth_domain)
        annotations = self._fetch_annotations(old_username)

        ids = set()
        for annotation in annotations:
            annotation.userid = new_userid
            ids.add(annotation.id)

        return ids

    def _fetch_annotations(self, username):
        userid = userid_from_username(username, self.auth_domain)
        return self.session.query(models.Annotation).filter(
            models.Annotation.userid == userid).yield_per(100)


def make_indexer(request):
    def _reindex(ids):
        if not ids:
            return

        request.tm.commit()
        indexer = index.BatchIndexer(request.db, request.es, request)
        indexer.index(ids)
    return _reindex


def rename_user_factory(context, request):
    """Return a RenameUserService instance for the passed context and request."""
    return RenameUserService(session=request.db,
                             auth_domain=request.auth_domain,
                             reindex=make_indexer(request))
