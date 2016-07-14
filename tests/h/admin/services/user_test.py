# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h import models
from h.admin.services.user import RenameUserService
from h.admin.services.user import UserRenameError
from h.util.user import userid_from_username


class TestRenameUserService(object):
    def test_check_returns_true_when_checks_are_successful(self, service, user):
        assert service.check(user.id, 'panda') is True

    def test_check_raises_when_user_id_cannot_be_found(self, service):
        with pytest.raises(UserRenameError) as err:
            service.check(1, 'luke')
        assert err.value.message == 'Could not find existing user with id "1"'

    def test_check_raises_when_new_userid_is_already_taken(self, service, user, db_session, factories):
        user_taken = factories.User(username='panda')
        db_session.add(user_taken)
        db_session.flush()

        with pytest.raises(UserRenameError) as err:
            service.check(user.id, 'panda')
        assert err.value.message == 'Another user already has the username "panda"'

    def test_rename_checks_first(self, service, check, user):
        service.rename(user.id, 'panda')

        check.assert_called_once_with(service, user.id, 'panda')

    def test_rename_changes_the_username(self, service, user, db_session):
        service.rename(user.id, 'panda')

        assert db_session.query(models.User).get(user.id).username == 'panda'

    @pytest.mark.usefixtures('index')
    def test_rename_changes_the_users_annotations_userid(self, service, user, annotations, db_session):
        service.rename(user.id, 'panda')

        expected = userid_from_username('panda', service.request.auth_domain)

        userids = [ann.userid for ann in db_session.query(models.Annotation)]
        assert set([expected]) == set(userids)

    def test_rename_reindexes_the_users_annotations(self, service, user, annotations, index):
        indexer = index.BatchIndexer.return_value
        ids = [ann.id for ann in annotations]

        service.rename(user.id, 'panda')

        indexer.index.assert_called_once_with(set(ids))

    @pytest.fixture
    def service(self, req):
        return RenameUserService(req)

    @pytest.fixture
    def check(self, patch):
        return patch('h.admin.services.user.RenameUserService.check')

    @pytest.fixture
    def req(self, pyramid_request):
        pyramid_request.tm = mock.MagicMock()
        pyramid_request.es = mock.MagicMock()
        return pyramid_request

    @pytest.fixture
    def user(self, factories, db_session):
        user = factories.User(username='giraffe')
        db_session.add(user)
        db_session.flush()
        return user

    @pytest.fixture
    def annotations(self, user, factories, db_session, req):
        anns = []
        for _ in range(8):
            userid = userid_from_username(user.username, req.auth_domain)
            anns.append(factories.Annotation(userid=userid))
        db_session.add_all(anns)
        db_session.flush()

        return anns

    @pytest.fixture
    def index(self, patch):
        return patch('h.admin.services.user.index')
