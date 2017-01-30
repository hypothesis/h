# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest


@pytest.mark.functional
class TestAPI(object):
    def test_annotation_read(self, app, annotation):
        """Fetch an annotation by ID."""
        res = app.get('/api/annotations/' + annotation.id,
                      headers={b'accept': b'application/json'})
        data = res.json
        assert data['id'] == annotation.id

    def test_annotation_read_jsonld(self, app, annotation):
        """Fetch an annotation by ID in jsonld format."""
        res = app.get('/api/annotations/' + annotation.id + '.jsonld')
        data = res.json
        assert data['@context'] == 'http://www.w3.org/ns/anno.jsonld'
        assert data['id'] == 'http://localhost/a/' + annotation.id

    def test_annotation_write_unauthorized_group(self, app, user_with_token, non_writeable_group):
        """
        Write an annotation to a group that doesn't allow writes.

        This is a basic test to check that h is correctly configuring the
        memex groupfinder. Because memex is permissive by default.
        """

        user, token = user_with_token

        headers = {'Authorization': str('Bearer {}'.format(token.value))}
        annotation = {
            'group': non_writeable_group.pubid,
            'permissions': {
                'read': ['group:{}'.format(non_writeable_group.pubid)],
                'admin': [user.userid],
                'update': [user.userid],
                'delete': [user.userid],
            },
            'text': 'My annotation',
            'uri': 'http://example.com',
        }

        res = app.post_json('/api/annotations', annotation, headers=headers, expect_errors=True)

        assert res.status_code == 400
        assert res.json['reason'].startswith('group:')

    def test_profile_api(self, app, user_with_token):
        """Fetch a profile through the API for an authenticated user."""

        user, token = user_with_token

        headers = {'Authorization': str('Bearer {}'.format(token.value))}

        res = app.get('/api/profile', headers=headers)

        assert res.json['userid'] == user.userid
        assert [group['id'] for group in res.json['groups']] == ['__world__']


@pytest.fixture
def annotation(db_session, factories):
    ann =  factories.Annotation(userid='acct:testuser@localhost',
                                groupid='__world__',
                                shared=True)
    db_session.commit()
    return ann


@pytest.fixture
def user(db_session, factories):
    user = factories.User()
    db_session.commit()
    return user


@pytest.fixture
def user_with_token(user, db_session, factories):
    token = factories.Token(userid=user.userid)
    db_session.add(token)
    db_session.commit()
    return (user, token)


@pytest.fixture
def non_writeable_group(db_session, factories):
    group = factories.Group(writeable_by=None)
    db_session.commit()
    return group
