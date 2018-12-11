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
class TestPutHide(object):
    def test_it_returns_http_204_for_group_creator(
        self, app, group_annotation, user_with_token
    ):
        user, token = user_with_token
        headers = {"Authorization": str("Bearer {}".format(token.value))}

        res = app.put(
            "/api/annotations/{id}/hide".format(id=group_annotation.id), headers=headers
        )

        # The creator of a group has moderation rights over the annotations in that group
        assert res.status_code == 204

    def test_it_returns_http_404_if_annotation_is_in_world_group(
        self, app, world_annotation, user_with_token
    ):
        user, token = user_with_token
        headers = {"Authorization": str("Bearer {}".format(token.value))}

        res = app.put(
            "/api/annotations/{id}/hide".format(id=world_annotation.id),
            headers=headers,
            expect_errors=True,
        )
        # The current user does not have moderation rights on the world group
        assert res.status_code == 404

    def test_it_returns_http_404_if_no_authn(self, app, group_annotation):

        res = app.put(
            "/api/annotations/{id}/hide".format(id=group_annotation.id),
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_http_404_if_annotation_is_private(
        self, app, private_group_annotation, user_with_token
    ):

        user, token = user_with_token
        headers = {"Authorization": str("Bearer {}".format(token.value))}

        res = app.put(
            "/api/annotations/{id}/hide".format(id=private_group_annotation.id),
            headers=headers,
            expect_errors=True,
        )
        # private annotations cannot be moderated
        assert res.status_code == 404


@pytest.mark.functional
class TestDeleteHide(object):
    def test_it_returns_http_204_for_group_creator(
        self, app, group_annotation, user_with_token
    ):
        user, token = user_with_token
        headers = {"Authorization": str("Bearer {}".format(token.value))}

        res = app.delete(
            "/api/annotations/{id}/hide".format(id=group_annotation.id), headers=headers
        )

        # The creator of a group has moderation rights over the annotations in that group
        assert res.status_code == 204

    def test_it_returns_http_404_if_annotation_is_in_world_group(
        self, app, world_annotation, user_with_token
    ):
        user, token = user_with_token
        headers = {"Authorization": str("Bearer {}".format(token.value))}

        res = app.delete(
            "/api/annotations/{id}/hide".format(id=world_annotation.id),
            headers=headers,
            expect_errors=True,
        )
        # The current user does not have moderation rights on the world group
        assert res.status_code == 404

    def test_it_returns_http_404_if_no_authn(self, app, group_annotation):

        res = app.delete(
            "/api/annotations/{id}/hide".format(id=group_annotation.id),
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_http_404_if_annotation_is_private(
        self, app, private_group_annotation, user_with_token
    ):

        user, token = user_with_token
        headers = {"Authorization": str("Bearer {}".format(token.value))}

        res = app.delete(
            "/api/annotations/{id}/hide".format(id=private_group_annotation.id),
            headers=headers,
            expect_errors=True,
        )
        # private annotations cannot be moderated
        assert res.status_code == 404


@pytest.fixture
def user(db_session, factories):
    user = factories.User()
    db_session.commit()
    return user


@pytest.fixture
def group(user, db_session, factories):
    group = factories.Group(creator=user)
    db_session.commit()
    return group


@pytest.fixture
def world_annotation(user, db_session, factories):
    ann = factories.Annotation(userid=user.userid, groupid="__world__", shared=True)
    db_session.commit()
    return ann


@pytest.fixture
def group_annotation(user, group, db_session, factories):
    ann = factories.Annotation(
        userid="acct:someone@example.com", groupid=group.pubid, shared=True
    )
    db_session.commit()
    return ann


@pytest.fixture
def private_group_annotation(user, group, db_session, factories):
    ann = factories.Annotation(
        userid="acct:someone@example.com", groupid=group.pubid, shared=False
    )
    db_session.commit()
    return ann


@pytest.fixture
def user_with_token(user, db_session, factories):
    token = factories.DeveloperToken(userid=user.userid)
    db_session.add(token)
    db_session.commit()
    return (user, token)
