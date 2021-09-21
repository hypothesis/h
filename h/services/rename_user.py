from h import models


class UserRenameError(Exception):
    pass


class RenameUserService:
    """
    Renames a user and updates all its annotations.

    ``check`` should be called first

    Validates the new username and updates the User. The user's annotations
    userid field will be updated. It accepts a reindex function that gets a
    list of annotation ids, it is then the function's responsibility to reindex
    these annotations in the search index.

    This also invalidates all authentication tickets, forcing the user to
    login again.

    May raise a ValueError if the new username does not validate or
    UserRenameError if the new username is already taken by another account.
    """

    def __init__(self, session, search_index):
        self.session = session
        self._search_index = search_index

    def check(self, user, new_username):
        existing_user = models.User.get_by_username(
            self.session, new_username, user.authority
        )
        if existing_user and existing_user != user:
            raise UserRenameError(
                f'Another user already has the username "{new_username}"'
            )

        return True

    def rename(self, user, new_username):
        self.check(user, new_username)

        old_userid = user.userid
        user.username = new_username
        new_userid = user.userid

        # Remove auth tickets when renaming the user. We cannot just update the
        # denormalized `user_userid` of these because the previous userid values
        # will have been serialized into the session cookies stored in the
        # user's browser. See
        # https://michael.merickel.org/projects/pyramid_auth_demo/auth_vs_auth.html
        self._purge_auth_tickets(user)

        # For OAuth tokens, only the token's value is stored by clients, so we
        # can just update the userid.
        self._update_tokens(old_userid, new_userid)

        self._change_annotations(old_userid, new_userid)
        self._search_index.add_users_annotations(
            old_userid,
            tag="RenameUserService.rename",
            schedule_in=30,
        )

    def _purge_auth_tickets(self, user):
        self.session.query(models.AuthTicket).filter(
            models.AuthTicket.user_id == user.id
        ).delete()

    def _update_tokens(self, old_userid, new_userid):
        self.session.query(models.Token).filter(
            models.Token.userid == old_userid
        ).update({"userid": new_userid}, synchronize_session="fetch")

    def _change_annotations(self, old_userid, new_userid):
        annotations = self._fetch_annotations(old_userid)

        for annotation in annotations:
            annotation.userid = new_userid

    def _fetch_annotations(self, userid):
        return (
            self.session.query(models.Annotation)
            .filter(models.Annotation.userid == userid)
            .yield_per(100)
        )


def rename_user_factory(_context, request):
    """Return a RenameUserService instance for the passed context and request."""
    return RenameUserService(
        session=request.db,
        search_index=request.find_service(name="search_index"),
    )
