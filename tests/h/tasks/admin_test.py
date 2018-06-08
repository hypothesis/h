# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.tasks.admin import rename_user


class TestRenameUser(object):
    def test_it_raises_when_user_cannot_be_found(self, celery):
        with pytest.raises(ValueError) as err:
            rename_user(4, "panda")
        assert str(err.value) == "Could not find user with id 4"

    def test_it_finds_the_service(self, celery, user):
        rename_user(user.id, "panda")

        celery.request.find_service.assert_called_once_with(name="rename_user")

    def test_it_renames_the_user(self, celery, user):
        service = celery.request.find_service.return_value

        rename_user(user.id, "panda")

        service.rename.assert_called_once_with(user, "panda")

    @pytest.fixture
    def user(self, factories, db_session):
        user = factories.User(username="giraffe")
        db_session.flush()
        return user

    @pytest.fixture
    def celery(self, patch, db_session):
        cel = patch("h.tasks.admin.celery", autospec=False)
        cel.request.db = db_session
        return cel
