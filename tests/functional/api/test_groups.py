# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import base64


from h.models.auth_client import GrantType

# String type for request/response headers and metadata in WSGI.
#
# Per PEP-3333, this is intentionally `str` under both Python 2 and 3, even
# though it has different meanings.
#
# See https://www.python.org/dev/peps/pep-3333/#a-note-on-string-types
native_str = str


@pytest.mark.functional
class TestCreateGroup(object):

    def test_it_returns_http_200_with_valid_payload(self, app, token_auth_header):
        group = {
            'name': 'My Group'
        }
        res = app.post_json('/api/groups', group, headers=token_auth_header)

        assert res.status_code == 200

    def test_it_returns_http_400_with_invalid_payload(self, app, token_auth_header):
        group = {}

        res = app.post_json('/api/groups', group, headers=token_auth_header, expect_errors=True)

        assert res.status_code == 400

    def test_it_returns_http_400_if_groupid_set_on_default_authority(self, app, token_auth_header):
        group = {
            'name': 'My Group',
            'groupid': '3434kjkjk',
        }
        res = app.post_json('/api/groups', group, headers=token_auth_header, expect_errors=True)

        assert res.status_code == 400

    def test_it_returns_http_404_if_no_authenticated_user(self, app, auth_client_header):
        # FIXME: This should return a 403
        group = {
            'name': 'My Group'
        }
        res = app.post_json('/api/groups', group, headers=auth_client_header, expect_errors=True)

        assert res.status_code == 404

    @pytest.mark.xfail
    def test_it_returns_http_403_if_no_authenticated_user(self, app, auth_client_header):
        group = {
            'name': 'My Group'
        }
        res = app.post_json('/api/groups', group, headers=auth_client_header, expect_errors=True)

        assert res.status_code == 403

    def test_it_allows_auth_client_with_forwarded_user(self, app, auth_client_header, third_party_user):
        headers = auth_client_header
        headers[native_str('X-Forwarded-User')] = native_str(third_party_user.userid)
        group = {
            'name': 'My Group'
        }

        res = app.post_json('/api/groups', group, headers=headers)

        assert res.status_code == 200

    def test_it_allows_groupdid_from_auth_client_with_forwarded_user(self, app, auth_client_header, third_party_user):
        headers = auth_client_header
        headers[native_str('X-Forwarded-User')] = native_str(third_party_user.userid)
        group = {
            'name': 'My Group',
            'groupid': 'group:333vcdfkj~@thirdparty.com',
        }

        res = app.post_json('/api/groups', group, headers=headers)
        data = res.json

        assert res.status_code == 200
        assert 'groupid' in data
        assert data['groupid'] == "group:{groupid}@thirdparty.com".format(groupid='333vcdfkj~')

    def test_it_returns_http_404_with_invalid_forwarded_user_format(self, app, auth_client_header):
        # FIXME: This should return a 403
        headers = auth_client_header
        headers[native_str('X-Forwarded-User')] = native_str('floopflarp')
        group = {}

        res = app.post_json('/api/groups', group, headers=headers, expect_errors=True)

        assert res.status_code == 404


@pytest.mark.functional
class TestAddMember(object):

    def test_it_returns_http_204_when_successful(self, app, third_party_user, third_party_group, auth_client_header):
        res = app.post_json("/api/groups/{pubid}/members/{userid}".format(pubid=third_party_group.pubid,
                                                                          userid=third_party_user.userid),
                                                                          headers=auth_client_header)

        assert res.status_code == 204

    def test_it_adds_member_to_group(self, app, third_party_user, third_party_group, auth_client_header):
        app.post_json("/api/groups/{pubid}/members/{userid}".format(pubid=third_party_group.pubid,
                                                                    userid=third_party_user.userid),
                                                                    headers=auth_client_header)

        assert third_party_user in third_party_group.members

    def test_it_ignores_forwarded_user_header(self, app, third_party_user, factories, third_party_group, db_session, auth_client_header):
        headers = auth_client_header
        user2 = factories.User(authority='thirdparty.com')
        db_session.commit()

        headers[native_str('X-Forwarded-User')] = native_str(third_party_user.userid)

        res = app.post_json("/api/groups/{pubid}/members/{userid}".format(pubid=third_party_group.pubid,
                                                                          userid=third_party_user.userid),
                                                                          headers=auth_client_header)

        assert third_party_user in third_party_group.members
        assert user2 not in third_party_group.members
        assert res.status_code == 204

    def test_it_is_idempotent(self, app, third_party_user, third_party_group, auth_client_header):
        app.post_json("/api/groups/{pubid}/members/{userid}".format(pubid=third_party_group.pubid,
                                                                    userid=third_party_user.userid),
                                                                    headers=auth_client_header)

        res = app.post_json("/api/groups/{pubid}/members/{userid}".format(pubid=third_party_group.pubid,
                                                                          userid=third_party_user.userid),
                                                                          headers=auth_client_header)

        assert third_party_user in third_party_group.members
        assert res.status_code == 204

    def test_it_returns_404_if_authority_mismatch_on_user(self, app, factories, group, auth_client_header):
        user = factories.User(authority="somewhere-else.org")
        res = app.post_json("/api/groups/{pubid}/members/{userid}".format(pubid=group.pubid, userid=user.userid),
                            headers=auth_client_header,
                            expect_errors=True)

        assert res.status_code == 404

    def test_it_returns_404_if_malformed_userid(self, app, factories, group, auth_client_header):
        res = app.post_json("/api/groups/{pubid}/members/{userid}".format(pubid=group.pubid, userid='foo@bar.com'),
                            headers=auth_client_header,
                            expect_errors=True)

        assert res.status_code == 404

    def test_it_returns_404_if_authority_mismatch_on_group(self, app, factories, user, auth_client_header):
        group = factories.Group(authority="somewhere-else.org")
        res = app.post_json("/api/groups/{pubid}/members/{userid}".format(pubid=group.pubid, userid=user.userid),
                            headers=auth_client_header,
                            expect_errors=True)

        assert res.status_code == 404

    def test_it_returns_404_if_missing_auth(self, app, user, group):
        res = app.post_json("/api/groups/{pubid}/members/{userid}".format(pubid=group.pubid, userid=user.userid),
                            expect_errors=True)

        assert res.status_code == 404

    def test_it_returns_404_with_token_auth(self, app, token_auth_header, user, group):
        res = app.post_json("/api/groups/{pubid}/members/{userid}".format(pubid=group.pubid, userid=user.userid),
                            headers=token_auth_header,
                            expect_errors=True)

        assert res.status_code == 404


@pytest.mark.functional
class TestRemoveMember(object):

    def test_it_removes_authed_user_from_group(self, app, group, group_member_with_token):

        group_member, token = group_member_with_token
        headers = {native_str('Authorization'): native_str('Bearer {}'.format(token.value))}

        app.delete('/api/groups/{}/members/me'.format(group.pubid),
                   headers=headers)

        # We currently have no elegant way to check this via the API, but in a
        # future version we should be able to make a GET request here for the
        # group information and check it 404s
        assert group_member not in group.members


@pytest.fixture
def user(db_session, factories):
    user = factories.User(authority='example.com')
    db_session.commit()
    return user


@pytest.fixture
def third_party_user(db_session, factories):
    user = factories.User(authority='thirdparty.com')
    db_session.commit()
    return user


@pytest.fixture
def auth_client(db_session, factories):
    auth_client = factories.ConfidentialAuthClient(authority='thirdparty.com',
                                                   grant_type=GrantType.client_credentials)
    db_session.commit()
    return auth_client


@pytest.fixture
def auth_client_header(auth_client):
    user_pass = "{client_id}:{secret}".format(client_id=auth_client.id, secret=auth_client.secret)
    encoded = base64.standard_b64encode(user_pass.encode('utf-8'))
    return {native_str('Authorization'): native_str("Basic {creds}".format(creds=encoded.decode('ascii')))}


@pytest.fixture
def group(db_session, factories):
    group = factories.Group()
    db_session.commit()
    return group


@pytest.fixture
def third_party_group(db_session, factories):
    group = factories.Group(authority='thirdparty.com')
    db_session.commit()
    return group


@pytest.fixture
def group_member(group, db_session, factories):
    user = factories.User()
    group.members.append(user)
    db_session.commit()
    return user


@pytest.fixture
def group_member_with_token(group_member, db_session, factories):
    token = factories.DeveloperToken(userid=group_member.userid)
    db_session.add(token)
    db_session.commit()
    return (group_member, token)


@pytest.fixture
def user_with_token(db_session, factories):
    user = factories.User()
    token = factories.DeveloperToken(userid=user.userid)
    db_session.add(token)
    db_session.commit()
    return (user, token)


@pytest.fixture
def token_auth_header(user_with_token):
    user, token = user_with_token
    return {native_str('Authorization'): native_str('Bearer {}'.format(token.value))}
