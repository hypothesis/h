# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest


@pytest.mark.functional
class TestGroupAPI(object):

    def test_create_group(self, app, user_with_token):
        """Test a request to create a private group through the API"""

        user, token = user_with_token
        headers = {'Authorization': str('Bearer {}'.format(token.value))}

        group = {
            'name': 'My Group'
        }

        res = app.post_json('/api/groups', group, headers=headers)

        assert res.status_code == 200
        assert res.json['name'] == 'My Group'

    def test_leave_group(self, app, group, group_member_with_token):
        """Test a request to leave a group through the API."""

        group_member, token = group_member_with_token
        headers = {'Authorization': str('Bearer {}'.format(token.value))}

        app.delete('/api/groups/{}/members/me'.format(group.pubid),
                   headers=headers)

        # We currently have no elegant way to check this via the API, but in a
        # future version we should be able to make a GET request here for the
        # group information and check it 404s
        assert group_member not in group.members


@pytest.fixture
def group(db_session, factories):
    group = factories.Group()
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
