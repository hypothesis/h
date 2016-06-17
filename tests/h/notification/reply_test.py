# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.models import Annotation
from h.models import Document, DocumentMeta
from h.models import Subscriptions
from h.models import User
from h.notification.reply import Notification
from h.notification.reply import get_notification

FIXTURE_DATA = {
    'reply': {
        'id': 'OECV3AmDEeaAtTt8rjCjIg',
        'groupid': '__world__',
        'shared': True,
        'userid': 'acct:elephant@safari.net',
    },
    'parent': {
        'id': 'SucHcAmDEeaAtf_ZeH-rhA',
        'groupid': '__world__',
        'shared': True,
        'userid': 'acct:giraffe@safari.net',
    },
}


@pytest.mark.usefixtures('authz_policy', 'fetch_annotation', 'get_user', 'subscription')
class TestGetNotification(object):
    def test_returns_correct_params_when_subscribed(self,
                                                    get_user,
                                                    parent,
                                                    pyramid_request,
                                                    reply):
        result = get_notification(pyramid_request, reply, 'create')

        assert isinstance(result, Notification)
        assert result.reply == reply
        assert result.parent == parent
        assert result.reply_user == get_user(reply.userid, pyramid_request)
        assert result.parent_user == get_user(parent.userid, pyramid_request)
        assert result.document == reply.document

    def test_returns_none_when_action_is_not_create(self, pyramid_request, reply):
        assert get_notification(pyramid_request, reply, 'update') is None
        assert get_notification(pyramid_request, reply, 'delete') is None
        assert get_notification(pyramid_request, reply, 'frobnicate') is None

    def test_returns_none_when_annotation_is_not_reply(self, pyramid_request, reply):
        reply.references = None

        result = get_notification(pyramid_request, reply, 'create')

        assert result is None

    def test_returns_none_when_parent_does_not_exist(self,
                                                     annotations,
                                                     parent,
                                                     pyramid_request,
                                                     reply):
        del annotations[parent.id]

        result = get_notification(pyramid_request, reply, 'create')

        assert result is None

    def test_returns_none_when_parent_user_does_not_exist(self, get_user, pyramid_request, reply):
        def _only_return_reply_user(userid, _):
            if userid == 'acct:elephant@safari.net':
                return User(username='elephant')
            return None
        get_user.side_effect = _only_return_reply_user

        result = get_notification(pyramid_request, reply, 'create')

        assert result is None

    def test_returns_none_when_reply_user_does_not_exist(self, get_user, pyramid_request, reply):
        """
        Don't send a reply if somehow the replying user ceased to exist.

        It's not clear when or why this would ever happen, but we can't
        construct the reply email without the user who replied existing. We log
        a warning if this happens.
        """
        def _only_return_parent_user(userid, _):
            if userid == 'acct:giraffe@safari.net':
                return User(username='giraffe')
            return None
        get_user.side_effect = _only_return_parent_user

        result = get_notification(pyramid_request, reply, 'create')

        assert result is None

    def test_returns_none_when_reply_by_same_user(self, parent, pyramid_request, reply):
        parent.userid = 'acct:elephant@safari.net'

        result = get_notification(pyramid_request, reply, 'create')

        assert result is None

    def test_returns_none_when_parent_user_cannot_read_reply(self, pyramid_request, reply):
        reply.shared = False

        result = get_notification(pyramid_request, reply, 'create')

        assert result is None

    def test_returns_none_when_subscription_inactive(self, pyramid_request, reply, subscription):
        subscription.active = False

        result = get_notification(pyramid_request, reply, 'create')

        assert result is None

    def test_returns_none_when_subscription_absent(self,
                                                   db_session,
                                                   parent,
                                                   pyramid_request,
                                                   reply):
        db_session.query(Subscriptions).delete()

        result = get_notification(pyramid_request, reply, 'create')

        assert result is None

    @pytest.fixture
    def annotations(self):
        return {}

    @pytest.fixture
    def authz_policy(self, pyramid_config):
        from pyramid.authorization import ACLAuthorizationPolicy
        pyramid_config.set_authorization_policy(ACLAuthorizationPolicy())

    @pytest.fixture
    def fetch_annotation(self, patch, annotations):
        fetch_annotation = patch('h.notification.reply.storage.fetch_annotation')
        fetch_annotation.side_effect = lambda _, id: annotations.get(id)
        return fetch_annotation

    @pytest.fixture
    def get_user(self, patch):
        users = {
            'acct:giraffe@safari.net': User(username='giraffe'),
            'acct:elephant@safari.net': User(username='elephant'),
        }
        get_user = patch('h.notification.reply.accounts.get_user')
        get_user.side_effect = lambda userid, _: users.get(userid)
        return get_user

    @pytest.fixture
    def parent(self, annotations):
        parent = Annotation(**FIXTURE_DATA['parent'])
        annotations[parent.id] = parent
        return parent

    @pytest.fixture
    def reply(self, annotations, db_session, parent):
        # We need to create a document object to provide the title, and
        # ensure it is associated with the annotation through the
        # annotation's `target_uri`
        doc = Document.find_or_create_by_uris(db_session,
                                              claimant_uri='http://example.net/foo',
                                              uris=[]).one()
        doc.meta.append(DocumentMeta(type='title',
                                     value=['Some document'],
                                     claimant='http://example.com/foo'))
        reply = Annotation(**FIXTURE_DATA['reply'])
        reply.target_uri = 'http://example.net/foo'
        reply.references = [parent.id]
        db_session.add(reply)
        db_session.flush()
        annotations[reply.id] = reply
        return reply

    @pytest.fixture
    def subscription(self, db_session):
        sub = Subscriptions(type='reply', active=True, uri='acct:giraffe@safari.net')
        db_session.add(sub)
        db_session.flush()
        return sub
