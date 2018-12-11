# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

# String type for request/response headers and metadata in WSGI.
#
# Per PEP-3333, this is intentionally `str` under both Python 2 and 3, even
# though it has different meanings.
#
# See https://www.python.org/dev/peps/pep-3333/#a-note-on-string-types
native_str = str


@pytest.mark.functional
class TestPutFlag(object):
    def test_it_returns_http_204_if_user_allowed_to_flag_shared_annotation(
        self, app, annotation, user_with_token
    ):
        user, token = user_with_token
        headers = {"Authorization": str("Bearer {}".format(token.value))}

        res = app.put(
            "/api/annotations/{id}/flag".format(id=annotation.id), headers=headers
        )

        # This annotation was not created by this user but it is a shared annotation
        assert res.status_code == 204

    def test_it_returns_http_204_if_user_allowed_to_flag_private_annotation(
        self, app, private_annotation, user_with_token
    ):

        user, token = user_with_token
        headers = {"Authorization": str("Bearer {}".format(token.value))}

        res = app.put(
            "/api/annotations/{id}/flag".format(id=private_annotation.id),
            headers=headers,
        )

        # This annotation was created by this user
        assert res.status_code == 204

    def test_it_returns_http_404_if_user_not_allowed_to_flag_private_annotation(
        self, app, unreadable_annotation, user_with_token
    ):

        user, token = user_with_token
        headers = {"Authorization": str("Bearer {}".format(token.value))}

        res = app.put(
            "/api/annotations/{id}/flag".format(id=unreadable_annotation.id),
            headers=headers,
            expect_errors=True,
        )

        # This private annotation was not created by this user
        assert res.status_code == 404

    def test_it_returns_http_404_if_unauthenticated(self, app, annotation):

        res = app.put(
            "/api/annotations/{id}/flag".format(id=annotation.id), expect_errors=True
        )

        assert res.status_code == 404


@pytest.fixture
def annotation(db_session, factories):
    ann = factories.Annotation(
        userid="acct:testuser@example.com", groupid="__world__", shared=True
    )
    db_session.commit()
    return ann


@pytest.fixture
def private_annotation(db_session, factories, user):
    ann = factories.Annotation(userid=user.userid, groupid="__world__", shared=False)
    db_session.commit()
    return ann


@pytest.fixture
def unreadable_annotation(db_session, factories):
    user = factories.User()
    ann = factories.Annotation(userid=user.userid, groupid="__world__", shared=False)
    db_session.commit()
    return ann


@pytest.fixture
def user(db_session, factories):
    user = factories.User()
    db_session.commit()
    return user


@pytest.fixture
def user_with_token(user, db_session, factories):
    token = factories.DeveloperToken(userid=user.userid)
    db_session.add(token)
    db_session.commit()
    return (user, token)
