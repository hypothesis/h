# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.presenters.user_json import UserJSONPresenter, TrustedUserJSONPresenter


class TestUserJSONPresenter(object):
    def test_asdict(self, user):
        presenter = UserJSONPresenter(user)

        assert presenter.asdict() == {
            "authority": user.authority,
            "userid": user.userid,
            "username": user.username,
            "display_name": user.display_name,
        }


class TestTrustedUserJSONPresenter(object):
    def test_asdict(self, user):
        presenter = TrustedUserJSONPresenter(user)

        assert presenter.asdict() == {
            "authority": user.authority,
            "userid": user.userid,
            "username": user.username,
            "display_name": user.display_name,
            "email": user.email,
        }


@pytest.fixture
def user(factories):
    return factories.User(
        authority="example.org",
        email="jack@doe.com",
        username="jack",
        display_name="Jack Doe",
    )
