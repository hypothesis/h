# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest


@pytest.mark.functional
class TestAPI(object):
    def test_api_index(self, app):
        """
        Test the API index view.

        This view is tested more thoroughly in the view tests, but this test
        checks the view doesn't error out and returns appropriate-looking JSON.
        """
        res = app.get('/api/')
        assert 'links' in res.json

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
        assert data['id'] == 'http://example.com/a/' + annotation.id

    def test_annotation_write_unauthorized_group(self, app, user_with_token, non_writeable_group):
        """
        Write an annotation to a group that doesn't allow writes.

        This is a basic test to check that h is correctly configuring the
        groupfinder.
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

    def test_anonymous_profile_api(self, app):
        """
        Fetch an anonymous "profile".

        With no authentication and no authority parameter, this should default
        to the site's `authority` and show only the global group.
        """

        res = app.get('/api/profile')

        assert res.json['userid'] is None
        assert res.json['authority'] == 'example.com'
        assert [group['id'] for group in res.json['groups']] == ['__world__']

    def test_profile_api(self, app, user_with_token):
        """Fetch a profile through the API for an authenticated user."""

        user, token = user_with_token

        headers = {'Authorization': str('Bearer {}'.format(token.value))}

        res = app.get('/api/profile', headers=headers)

        assert res.json['userid'] == user.userid
        assert [group['id'] for group in res.json['groups']] == ['__world__']

    def test_third_party_profile_api(self, app, open_group, third_party_user_with_token):
        """Fetch a profile for a third-party account."""

        user, token = third_party_user_with_token

        headers = {'Authorization': str('Bearer {}'.format(token.value))}

        res = app.get('/api/profile', headers=headers)

        assert res.json['userid'] == user.userid

        group_ids = [group['id'] for group in res.json['groups']]
        assert group_ids == [open_group.pubid]

    def test_cors_preflight(self, app):
        # Simulate a CORS preflight request made by the browser from a client
        # hosted on a domain other than the one the service is running on.
        #
        # Note that no `Authorization` header is set.
        origin = 'https://custom-client.herokuapp.com'
        headers = {'Access-Control-Request-Headers': str('authorization,content-type'),
                   'Access-Control-Request-Method': str('POST'),
                   'Origin': str(origin)}

        res = app.options('/api/annotations', headers=headers)

        assert res.status_code == 200
        assert res.headers['Access-Control-Allow-Origin'] == str(origin)
        assert 'POST' in res.headers['Access-Control-Allow-Methods']
        for header in ['Authorization', 'Content-Type', 'X-Client-Id']:
            assert header in res.headers['Access-Control-Allow-Headers']


@pytest.fixture
def annotation(db_session, factories):
    ann = factories.Annotation(userid='acct:testuser@example.com',
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
    token = factories.DeveloperToken(userid=user.userid)
    db_session.add(token)
    db_session.commit()
    return (user, token)


@pytest.fixture
def auth_client(db_session, factories):
    auth_client = factories.AuthClient(authority='thirdparty.example.org')
    db_session.commit()
    return auth_client


@pytest.fixture
def third_party_user(auth_client, db_session, factories):
    user = factories.User(authority=auth_client.authority)
    db_session.commit()
    return user


@pytest.fixture
def open_group(auth_client, db_session, factories):
    group = factories.OpenGroup(authority=auth_client.authority)
    db_session.commit()
    return group


@pytest.fixture
def third_party_user_with_token(third_party_user, db_session, factories):
    token = factories.DeveloperToken(userid=third_party_user.userid)
    db_session.commit()
    return (third_party_user, token)


@pytest.fixture
def non_writeable_group(db_session, factories):
    group = factories.Group(writeable_by=None)
    db_session.commit()
    return group
