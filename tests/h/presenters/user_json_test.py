# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.presenters.user_json import UserJSONPresenter


class TestUserJSONPresenter(object):
    def test_asdict(self, factories):
        user = factories.User(
            authority="example.org",
            email="jack@doe.com",
            username="jack",
            display_name="Jack Doe",
        )
        presenter = UserJSONPresenter(user)

        assert presenter.asdict() == {
            "authority": "example.org",
            "email": "jack@doe.com",
            "userid": "acct:jack@example.org",
            "username": "jack",
            "display_name": "Jack Doe",
        }
