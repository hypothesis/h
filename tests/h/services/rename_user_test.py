from unittest import mock

import pytest

from h import models
from h.services.rename_user import RenameUserService, UserRenameError


class TestRenameUserService:
    def test_check_returns_true_when_new_username_does_not_exist(self, service, user):
        assert service.check(user, "panda") is True

    def test_check_raises_when_new_userid_is_already_taken(
        self, service, user, db_session, factories
    ):
        factories.User(username="panda")
        db_session.flush()

        with pytest.raises(UserRenameError) as err:
            service.check(user, "panda")
        assert str(err.value) == 'Another user already has the username "panda"'

    @mock.patch("h.models.user.User.get_by_username")
    def test_check_returns_True_if_new_username_equivalent_to_old(
        self, get_by_username, service, user
    ):
        """
        check() should return True if the new username is equivalent to the old.

        It's possible to have two different usernames, for example "bob.smith"
        and "Bob.Smith", that are "equivalent" in that they both reduce to the
        same normalised username "bobsmith". While we can't allow two
        different users to have the usernames "bob.smith" and "Bob.Smith", we
        _should_ allow renaming a single "bob.smith" user to "Bob.Smith".

        get_by_username() returns a User whose username is the same as or
        equivalent to the given username. If the returned User is the same user
        who we're trying to rename, we should allow the rename operation to go
        ahead.

        """
        get_by_username.return_value = user

        assert service.check(user, "panda") is True

    def test_rename_checks_first(self, service, check, user):
        service.rename(user, "panda")

        check.assert_called_once_with(service, user, "panda")

    def test_rename_changes_the_username(self, service, user, db_session):
        service.rename(user, "panda")

        assert db_session.query(models.User).get(user.id).username == "panda"

    def test_rename_deletes_auth_tickets(self, service, user, db_session, factories):
        ids = [factories.AuthTicket(user=user).id for _ in range(3)]

        service.rename(user, "panda")

        count = (
            db_session.query(models.AuthTicket)
            .filter(models.AuthTicket.id.in_(ids))
            .count()
        )
        assert not count

    def test_rename_updates_tokens(self, service, user, db_session):
        token = models.Token(userid=user.userid, value="foo")
        db_session.add(token)

        service.rename(user, "panda")

        updated_token = (
            db_session.query(models.Token).filter(models.Token.id == token.id).one()
        )
        assert updated_token.userid == user.userid

    @pytest.mark.usefixtures("annotations")
    def test_rename_changes_the_users_annotations_userid(
        self, service, user, db_session
    ):
        service.rename(user, "panda")

        userids = [ann.userid for ann in db_session.query(models.Annotation)]
        assert {user.userid} == set(userids)

    def test_rename_reindexes_the_users_annotations(self, service, user, search_index):
        original_userid = user.userid

        service.rename(user, "panda")

        search_index.add_users_annotations.assert_called_once_with(
            original_userid,
            tag="RenameUserService.rename",
            schedule_in=30,
        )

    @pytest.fixture
    def service(self, pyramid_request, search_index):
        return RenameUserService(session=pyramid_request.db, search_index=search_index)

    @pytest.fixture
    def check(self, patch):
        return patch("h.services.rename_user.RenameUserService.check")

    @pytest.fixture
    def user(self, factories, db_session):
        user = factories.User(username="giraffe")
        db_session.flush()
        return user

    @pytest.fixture
    def annotations(self, user, factories, db_session):
        anns = []
        for _ in range(8):
            anns.append(factories.Annotation(userid=user.userid))
        db_session.add_all(anns)
        db_session.flush()

        return anns
