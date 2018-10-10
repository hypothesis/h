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
class TestGetAnnotations(object):
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
                      headers={native_str('accept'): native_str('application/json')})
        data = res.json
        assert data['id'] == annotation.id

    def test_annotation_read_jsonld(self, app, annotation):
        """Fetch an annotation by ID in jsonld format."""
        res = app.get('/api/annotations/' + annotation.id + '.jsonld')
        data = res.json
        assert data['@context'] == 'http://www.w3.org/ns/anno.jsonld'
        assert data['id'] == 'http://example.com/a/' + annotation.id


class TestPostAnnotation(object):
    def test_it_returns_http_404_if_unauthorized(self, app):
        # FIXME: This should return a 403

        # This isn't a valid payload, but it won't get validated because the
        # authorization will fail first
        annotation = {
            'text': 'My annotation',
            'uri': 'http://example.com',
        }

        res = app.post_json('/api/annotations', annotation, expect_errors=True)

        assert res.status_code == 404

    @pytest.mark.xfail
    def test_it_returns_http_403_if_unauthorized(self, app):
        annotation = {
            'text': 'My annotation',
            'uri': 'http://example.com',
        }

        res = app.post_json('/api/annotations', annotation, expect_errors=True)

        assert res.status_code == 403

    def test_it_returns_http_400_if_group_forbids_write(self, app, user_with_token, non_writeable_group):
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
def non_writeable_group(db_session, factories):
    group = factories.Group(writeable_by=None)
    db_session.commit()
    return group
