# -*- coding: utf-8 -*-
"""Defines unit tests for h.notifier."""

from mock import patch, Mock

import pytest
from pyramid.testing import DummyRequest

from h.api import storage
from h.notification import reply_template as rt

store_fake_data = [
    {
        # Root (parent)
        'id': '0',
        'created': '2013-10-27T19:40:53.245691+00:00',
        'document': {'title': 'How to reach the ark NOW?'},
        'group': '__world__',
        'text': 'The animals went in two by two, hurrah! hurrah!',
        'permissions': {'read': ['group:__world__']},
        'uri': 'www.howtoreachtheark.now',
        'user': 'acct:elephant@nomouse.pls'
    },
    {
        # Reply
        'id': '1',
        'created': '2014-10-27T19:50:53.245691+00:00',
        'document': {'title': 'How to reach the ark NOW?'},
        'group': '__world__',
        'text': 'The animals went in three by three, hurrah! hurrah',
        'permissions': {'read': ['group:__world__']},
        'references': [0],
        'uri': 'www.howtoreachtheark.now',
        'user': 'acct:wasp@stinger.rulz'
    },
    {
        # Reply_of_reply
        'id': '2',
        'created': '2014-10-27T19:55:53.245691+00:00',
        'document': {'title': 'How to reach the ark NOW?'},
        'group': '__world__',
        'text': 'The animals went in four by four, hurrah! hurrah',
        'permissions': {'read': ['group:__world__']},
        'references': [0, 1],
        'uri': 'www.howtoreachtheark.now',
        'user': 'acct:hippopotamus@stucked.sos'
    },
    {
        # Reply to the root with the same user
        'id': '3',
        'created': '2014-10-27T20:40:53.245691+00:00',
        'document': {'title': 'How to reach the ark NOW?'},
        'group': '__world__',
        'text': 'The animals went in two by two, hurrah! hurrah!',
        'permissions': {'read': ['group:__world__']},
        'references': [0],
        'uri': 'www.howtoreachtheark.now',
        'user': 'acct:elephant@nomouse.pls'
    },
    {
        # Reply to the root with the same user
        'id': '4',
        'created': '2014-10-27T20:40:53.245691+00:00',
        'document': {'title': ''},
        'group': '__world__',
        'text': 'The animals went in two by two, hurrah! hurrah!',
        'permissions': {'read': ['group:__world__']},
        'references': [0],
        'uri': 'www.howtoreachtheark.now',
        'user': 'acct:elephant@nomouse.pls'
    },
    {
        # A thread root for testing permissions
        'id': '5',
        'user': 'acct:amrit@example.org'
    },
    {
        # A reply for testing permissions
        'id': '6',
        'permissions': {'read': ['acct:jane@example.com']},
        'references': [5],
        'user': 'acct:jane@example.com'
    },
    {
        # A reply for testing permissions
        'id': '7',
        'document': {'title': ''},
        'group': 'wibble',
        'permissions': {'read': ['acct:jane@example.com', 'group:wibble']},
        'references': [5],
        'user': 'acct:jane@example.com'
    },
]


def _fake_request():
    mock_dumps = Mock(return_value='TOKEN')
    request = DummyRequest()
    request.domain = 'www.howtoreachtheark.now'
    request.registry.notification_serializer = Mock(dumps=mock_dumps)
    request.route_url = Mock()
    request.route_url.return_value = 'UNSUBSCRIBE_URL'
    return request


def _fake_anno(id):
    try:
        offset = int(id)
    except TypeError:
        return None
    return storage.annotation_from_dict(store_fake_data[offset])


class MockSubscription(Mock):
    def __json__(self, request):
        return {
            'id': self.id or '',
            'uri': self.uri or ''
        }


# Tests for the check_conditions function
def test_dont_send_to_the_same_user():
    """Tests that if the parent user and the annotation user is the same
    then this function returns False"""
    annotation = _fake_anno(3)
    data = {
        'parent': _fake_anno(0),
        'subscription': {'id': 1}
    }

    send = rt.check_conditions(annotation, data)
    assert send is False


def test_different_subscription():
    """If subscription.uri is different from user, do not send!"""
    annotation = _fake_anno(1)
    data = {
        'parent': _fake_anno(0),
        'subscription': {
            'id': 1,
            'uri': 'acct:hippopotamus@stucked.sos'
        }
    }

    send = rt.check_conditions(annotation, data)
    assert send is False


def test_good_conditions():
    """If conditions match, this function returns with a True value"""
    annotation = _fake_anno(1)
    data = {
        'parent': _fake_anno(0),
        'subscription': {
            'id': 1,
            'uri': 'acct:elephant@nomouse.pls'
        }
    }

    send = rt.check_conditions(annotation, data)
    assert send is True


generate_notifications_fixtures = pytest.mark.usefixtures('auth', 'get_user')


@generate_notifications_fixtures
def test_generate_notifications_empty_if_action_not_create():
    """If the action is not 'create', no notifications should be generated."""
    annotation = storage.annotation_from_dict({})
    request = DummyRequest()

    notifications = rt.generate_notifications(request, annotation, 'update')

    assert list(notifications) == []


@generate_notifications_fixtures
def test_generate_notifications_empty_if_annotation_has_no_parent():
    """If the annotation has no parent no notifications should be generated."""
    annotation = _fake_anno(0)
    request = DummyRequest()

    notifications = rt.generate_notifications(request, annotation, 'create')

    assert list(notifications) == []


@generate_notifications_fixtures
def test_generate_notifications_does_not_fetch_if_annotation_has_no_parent(fetch):
    """Don't try and fetch None if the annotation has no parent"""
    annotation = _fake_anno(0)
    request = DummyRequest()

    notifications = rt.generate_notifications(request, annotation, 'create')

    # Read the generator
    list(notifications)

    fetch.assert_not_called()


@generate_notifications_fixtures
@patch('h.notification.reply_template.Subscriptions')
def test_generate_notifications_only_if_author_can_read_reply(
        Subscriptions,
        auth):
    """
    If the annotation is not readable by the parent author, no notifications
    should be generated.
    """
    Subscriptions.get_active_subscriptions_for_a_type.return_value = [
        MockSubscription(id=1, uri='acct:amrit@example.org')
    ]

    auth.has_permission.return_value = False
    notifications = rt.generate_notifications(_fake_request(),
                                              _fake_anno(6),
                                              'create')
    assert list(notifications) == []

    auth.has_permission.return_value = True
    notifications = rt.generate_notifications(_fake_request(),
                                              _fake_anno(7),
                                              'create')
    assert list(notifications) != []


@generate_notifications_fixtures
@patch('h.notification.reply_template.Subscriptions')
def test_generate_notifications_checks_subscriptions(Subscriptions):
    """If the annotation has a parent, then proceed to check subscriptions."""
    request = _fake_request()
    annotation = _fake_anno(1)
    Subscriptions.get_active_subscriptions_for_a_type.return_value = []

    notifications = rt.generate_notifications(request, annotation, 'create')

    # Read the generator
    list(notifications)

    Subscriptions.get_active_subscriptions_for_a_type.assert_called_with('reply')


@generate_notifications_fixtures
def test_check_conditions_false_stops_sending():
    """If the check conditions() returns False, no notifications are generated"""
    request = _fake_request()
    annotation = _fake_anno(1)

    with patch('h.notification.reply_template.Subscriptions') as mock_subs:
        mock_subs.get_active_subscriptions_for_a_type.return_value = [
            MockSubscription(id=1, uri='acct:elephant@nomouse.pls')
        ]
        with patch('h.notification.reply_template.check_conditions') as mock_conditions:
            mock_conditions.return_value = False
            with pytest.raises(StopIteration):
                msgs = rt.generate_notifications(request, annotation, 'create')
                msgs.next()


@generate_notifications_fixtures
def test_send_if_everything_is_okay():
    """Test whether we generate notifications if every condition is okay"""
    request = _fake_request()
    annotation = _fake_anno(1)

    with patch('h.notification.reply_template.Subscriptions') as mock_subs:
        mock_subs.get_active_subscriptions_for_a_type.return_value = [
            MockSubscription(id=1, uri='acct:elephant@nomouse.pls')
        ]
        with patch('h.notification.reply_template.check_conditions') as mock_conditions:
            mock_conditions.return_value = True
            msgs = rt.generate_notifications(request, annotation, 'create')
            msgs.next()


@pytest.fixture
def auth(patch):
    return patch('h.notification.reply_template.auth')


@pytest.fixture
def get_user(patch):
    return patch('h.notification.reply_template.accounts.get_user')


@pytest.fixture(autouse=True)
def fetch(request):
    patcher = patch.object(storage, 'fetch_annotation')
    fetch = patcher.start()
    fetch.side_effect = lambda _, id: _fake_anno(id)
    request.addfinalizer(patcher.stop)
    return fetch
