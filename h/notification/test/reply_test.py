# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
from pyramid.testing import DummyRequest

from h import db
from h.api.models import elastic
from h.models import Annotation
from h.models import Document, DocumentMeta
from h.models import Subscriptions
from h.models import User
from h.notification.reply import Notification
from h.notification.reply import get_notification

FIXTURE_DATA = {
    'reply_elastic': {
        'id': 'OECV3AmDEeaAtTt8rjCjIg',
        'group': '__world__',
        'permissions': {'read': ['group:__world__']},
        'user': 'acct:elephant@safari.net',
    },
    'parent_elastic': {
        'id': 'SucHcAmDEeaAtf_ZeH-rhA',
        'group': '__world__',
        'permissions': {'read': ['group:__world__']},
        'user': 'acct:giraffe@safari.net',
    },
    'reply_postgres': {
        'id': 'OECV3AmDEeaAtTt8rjCjIg',
        'groupid': '__world__',
        'shared': True,
        'userid': 'acct:elephant@safari.net',
    },
    'parent_postgres': {
        'id': 'SucHcAmDEeaAtf_ZeH-rhA',
        'groupid': '__world__',
        'shared': True,
        'userid': 'acct:giraffe@safari.net',
    },
}


@pytest.mark.usefixtures('authz_policy', 'fetch_annotation', 'get_user', 'subscription')
class TestGetNotification(object):
    def test_returns_correct_params_when_subscribed(self, get_user, reply, parent):
        request = DummyRequest(db=db.Session)

        result = get_notification(request, reply, 'create')

        assert isinstance(result, Notification)
        assert result.reply == reply
        assert result.parent == parent
        assert result.reply_user == get_user(reply.userid, request)
        assert result.parent_user == get_user(parent.userid, request)
        assert result.document == reply.document

    def test_returns_none_when_action_is_not_create(self, reply):
        request = DummyRequest(db=db.Session)

        assert get_notification(request, reply, 'update') is None
        assert get_notification(request, reply, 'delete') is None
        assert get_notification(request, reply, 'frobnicate') is None

    def test_returns_none_when_annotation_is_not_reply(self, reply, storage_driver):
        request = DummyRequest(db=db.Session)
        if storage_driver == 'elastic':
            del reply['references']
        else:
            reply.references = None

        result = get_notification(request, reply, 'create')

        assert result is None

    def test_returns_none_when_parent_does_not_exist(self, annotations, reply, parent):
        request = DummyRequest(db=db.Session)
        del annotations[parent.id]

        result = get_notification(request, reply, 'create')

        assert result is None

    def test_returns_none_when_parent_user_does_not_exist(self, get_user, reply):
        request = DummyRequest(db=db.Session)

        def _only_return_reply_user(userid, _):
            if userid == 'acct:elephant@safari.net':
                return User(username='elephant')
            return None
        get_user.side_effect = _only_return_reply_user

        result = get_notification(request, reply, 'create')

        assert result is None

    def test_returns_none_when_reply_user_does_not_exist(self, get_user, reply):
        """
        Don't send a reply if somehow the replying user ceased to exist.

        It's not clear when or why this would ever happen, but we can't
        construct the reply email without the user who replied existing. We log
        a warning if this happens.
        """
        request = DummyRequest(db=db.Session)

        def _only_return_parent_user(userid, _):
            if userid == 'acct:giraffe@safari.net':
                return User(username='giraffe')
            return None
        get_user.side_effect = _only_return_parent_user

        result = get_notification(request, reply, 'create')

        assert result is None

    def test_returns_none_when_reply_by_same_user(self, reply, parent, storage_driver):
        request = DummyRequest(db=db.Session)
        if storage_driver == 'elastic':
            parent['user'] = 'acct:elephant@safari.net'
        else:
            parent.userid = 'acct:elephant@safari.net'

        result = get_notification(request, reply, 'create')

        assert result is None

    def test_returns_none_when_parent_user_cannot_read_reply(self, reply, storage_driver):
        request = DummyRequest(db=db.Session)
        if storage_driver == 'elastic':
            reply['permissions'] = {'read': ['acct:elephant@safari.net']}
        else:
            reply.shared = False

        result = get_notification(request, reply, 'create')

        assert result is None

    def test_returns_none_when_subscription_inactive(self, reply, subscription):
        request = DummyRequest(db=db.Session)
        subscription.active = False

        result = get_notification(request, reply, 'create')

        assert result is None

    def test_returns_none_when_subscription_absent(self, reply, parent, subscription):
        request = DummyRequest(db=db.Session)
        db.Session.delete(subscription)

        result = get_notification(request, reply, 'create')

        assert result is None

    @pytest.fixture
    def annotations(self):
        return {}

    @pytest.fixture
    def authz_policy(self, config):
        from pyramid.authorization import ACLAuthorizationPolicy
        config.set_authorization_policy(ACLAuthorizationPolicy())

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
    def parent(self, annotations, storage_driver):
        if storage_driver == 'elastic':
            parent = elastic.Annotation(**FIXTURE_DATA['parent_elastic'])
        else:
            parent = Annotation(**FIXTURE_DATA['parent_postgres'])
        annotations[parent.id] = parent
        return parent

    @pytest.fixture
    def reply(self, annotations, storage_driver, parent):
        if storage_driver == 'elastic':
            reply = elastic.Annotation(**FIXTURE_DATA['reply_elastic'])
            reply['document'] = {'title': ['Some document']}
            reply['references'] = [parent.id]
        else:
            # We need to create a document object to provide the title, and
            # ensure it is associated with the annotation through the
            # annotation's `target_uri`
            doc = Document.find_or_create_by_uris(db.Session,
                                                  claimant_uri='http://example.net/foo',
                                                  uris=[]).one()
            doc.meta.append(DocumentMeta(type='title',
                                         value=['Some document'],
                                         claimant='http://example.com/foo'))
            reply = Annotation(**FIXTURE_DATA['reply_postgres'])
            reply.target_uri = 'http://example.net/foo'
            reply.references = [parent.id]
            db.Session.add(reply)
            db.Session.flush()
        annotations[reply.id] = reply
        return reply

    @pytest.fixture(params=['elastic', 'postgres'])
    def storage_driver(self, request):
        return request.param

    @pytest.fixture
    def subscription(self):
        sub = Subscriptions(type='reply', active=True, uri='acct:giraffe@safari.net')
        db.Session.add(sub)
        db.Session.flush()
        return sub
