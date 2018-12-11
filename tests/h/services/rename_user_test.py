# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h._compat import xrange

import mock
import pytest

from h import models
from h.services.rename_user import make_indexer, RenameUserService, UserRenameError


class TestRenameUserService(object):
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
        ids = [factories.AuthTicket(user=user).id for _ in xrange(3)]

        service.rename(user, "panda")

        count = (
            db_session.query(models.AuthTicket)
            .filter(models.AuthTicket.id.in_(ids))
            .count()
        )
        assert count == 0

    def test_rename_updates_tokens(self, service, user, db_session, factories):
        token = models.Token(userid=user.userid, value="foo")
        db_session.add(token)

        service.rename(user, "panda")

        updated_token = (
            db_session.query(models.Token).filter(models.Token.id == token.id).one()
        )
        assert updated_token.userid == user.userid

    def test_rename_changes_the_users_annotations_userid(
        self, service, user, annotations, db_session
    ):
        service.rename(user, "panda")

        userids = [ann.userid for ann in db_session.query(models.Annotation)]
        assert set([user.userid]) == set(userids)

    def test_rename_reindexes_the_users_annotations(
        self, service, user, annotations, indexer
    ):
        service.rename(user, "panda")
        indexer.assert_called_once_with({ann.id for ann in annotations})

    @pytest.fixture
    def indexer(self):
        return mock.Mock(spec_set=[])

    @pytest.fixture
    def service(self, pyramid_request, indexer):
        return RenameUserService(session=pyramid_request.db, reindex=indexer)

    @pytest.fixture
    def check(self, patch):
        return patch("h.services.rename_user.RenameUserService.check")

    @pytest.fixture
    def user(self, factories, db_session):
        user = factories.User(username="giraffe")
        db_session.flush()
        return user

    @pytest.fixture
    def annotations(self, user, factories, db_session, pyramid_request):
        anns = []
        for _ in range(8):
            anns.append(factories.Annotation(userid=user.userid))
        db_session.add_all(anns)
        db_session.flush()

        return anns


class TestMakeIndexer(object):
    def test_it_indexes_the_given_ids(self, req, index):
        indexer = make_indexer(req)
        indexer([1, 2, 3])

        batch_indexer = index.BatchIndexer.return_value
        batch_indexer.index.assert_called_once_with([1, 2, 3])
        index.BatchIndexer.assert_any_call(req.db, req.es, req)

    def test_it_skips_indexing_when_no_ids_given(self, req, index):
        indexer = make_indexer(req)

        indexer([])

        assert not index.BatchIndexer.called

    @pytest.fixture
    def req(self, pyramid_request):
        pyramid_request.tm = mock.MagicMock()
        pyramid_request.es = mock.MagicMock()
        return pyramid_request

    @pytest.fixture
    def index(self, patch):
        return patch("h.services.rename_user.index")
