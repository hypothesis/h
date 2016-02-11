# -*- coding: utf-8 -*-
"""Defines unit tests for h.notifier."""
from mock import patch, Mock, MagicMock

import pytest
from pyramid.testing import DummyRequest
from pyramid import security

from h.api import storage
from h.notification.gateway import user_name, user_profile_url, standalone_url
from h.notification import reply_template as rt
from h.notification.types import REPLY_TYPE

store_fake_data = [
    {
        # Root (parent)
        'id': '0',
        'created': '2013-10-27T19:40:53.245691+00:00',
        'document': {'title': 'How to reach the ark NOW?'},
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


# Tests for the parent_values function
def test_parent_values_reply():
    """Test if the function gives back the correct parent_value"""
    annotation = _fake_anno(1)
    parent = rt.parent_values(annotation)

    assert parent['id'] == '0'


def test_parent_values_root_annotation():
    """Test if it gives back an empty dict for root annotations"""
    annotation = _fake_anno(0)
    parent = rt.parent_values(annotation)

    assert len(parent.items()) == 0


# Tests for the create_template_map function
def test_all_keys_are_there():
    """Checks for the existence of every needed key for the template"""
    request = _fake_request()
    annotation = _fake_anno(1)

    parent = rt.parent_values(annotation)
    tmap = rt.create_template_map(request, annotation, parent)

    assert 'document_title' in tmap
    assert 'document_path' in tmap
    assert 'parent_text' in tmap
    assert 'parent_user' in tmap
    assert 'parent_timestamp' in tmap
    assert 'parent_user_profile' in tmap
    assert 'parent_path' in tmap
    assert 'reply_text' in tmap
    assert 'reply_user' in tmap
    assert 'reply_timestamp' in tmap
    assert 'reply_user_profile' in tmap
    assert 'reply_path' in tmap
    assert 'unsubscribe' in tmap


def test_template_map_key_values():
    """This test checks whether the keys holds the correct values"""
    request = _fake_request()
    annotation = _fake_anno(1)

    parent = rt.parent_values(annotation)
    tmap = rt.create_template_map(request, annotation, parent)

    parent = _fake_anno(0)

    # Document properties
    assert tmap['document_title'] == annotation['document']['title']
    assert tmap['document_path'] == parent['uri']

    # Parent properties
    assert tmap['parent_text'] == parent['text']
    assert tmap['parent_user'] == user_name(parent['user'])
    assert tmap['parent_user_profile'] == user_profile_url(request, parent['user'])
    assert tmap['parent_path'] == standalone_url(request, parent['id'])

    # Annotation properties
    assert tmap['reply_text'] == annotation['text']
    assert tmap['reply_user'] == user_name(annotation['user'])
    assert tmap['reply_user_profile'] == user_profile_url(request, annotation['user'])
    assert tmap['reply_path'] == standalone_url(request, annotation['id'])

    assert tmap['parent_timestamp'] == '27 October 2013 at 19:40'
    assert tmap['reply_timestamp'] == '27 October 2014 at 19:50'

    assert tmap['unsubscribe'] == 'UNSUBSCRIBE_URL'


def test_create_template_map_when_parent_has_no_text():
    """It shouldn't crash if the parent annotation has no 'text' item."""
    rt.create_template_map(
            Mock(application_url='https://hypothes.is'),
        reply={
            'document': {
                'title': 'Document Title'
            },
            'user': 'acct:bob@hypothes.is',
            'text': "This is Bob's annotation",
            'created': '2013-10-27T19:40:53.245691+00:00',
            'id': '0'
        },
        # parent dict has no 'text' item.
        parent={
            'uri': 'http://example.com/example.html',
            'user': 'acct:fred@hypothes.is',
            'created': '2013-10-27T19:40:53.245691+00:00',
            'id': '1'
        })


def test_fallback_title():
    """Checks that the title falls back to using the url"""
    request = _fake_request()
    annotation = _fake_anno(4)

    parent = rt.parent_values(annotation)
    tmap = rt.create_template_map(request, annotation, parent)
    assert tmap['document_title'] == annotation['uri']


def test_unsubscribe_token_generation():
    """ensures that a serialized token is generated for the unsubscribe url"""
    request = _fake_request()
    annotation = _fake_anno(4)

    parent = rt.parent_values(annotation)
    rt.create_template_map(request, annotation, parent)

    notification_serializer = request.registry.notification_serializer
    notification_serializer.dumps.assert_called_with({
        'type': REPLY_TYPE,
        'uri': parent['user'],
    })


def test_unsubscribe_url_generation():
    """ensures that a serialized token is generated for the unsubscribe url"""
    request = _fake_request()
    annotation = _fake_anno(4)

    parent = rt.parent_values(annotation)
    rt.create_template_map(request, annotation, parent)

    request.route_url.assert_called_with('unsubscribe', token='TOKEN')

# Tests for the get_recipients function
def test_get_email():
    """Tests whether it gives back the user.email property"""
    with patch('h.notification.reply_template.get_user_by_name') as mock_user_db:
        user = Mock()
        user.email = 'testmail@test.com'
        mock_user_db.return_value = user
        request = _fake_request()

        annotation = _fake_anno(1)
        parent = rt.parent_values(annotation)

        email = rt.get_recipients(request, parent)
        assert email[0] == user.email


def test_no_email():
    """If user has no email we must throw an exception"""
    with patch('h.notification.reply_template.get_user_by_name') as mock_user_db:
        mock_user_db.return_value = {}
        request = _fake_request()

        annotation = _fake_anno(1)
        parent = rt.parent_values(annotation)

        exc = False
        try:
            rt.get_recipients(request, parent)
        except:
            exc = True
        assert exc


# Tests for the check_conditions function
def test_dont_send_to_the_same_user():
    """Tests that if the parent user and the annotation user is the same
    then this function returns False"""
    annotation = _fake_anno(0)
    data = {
        'parent': rt.parent_values(annotation),
        'subscription': {'id': 1}
    }

    send = rt.check_conditions(annotation, data)
    assert send is False


def test_dont_send_if_parent_is_missing():
    """Tests that this function returns False if the annotations parent's user is missing"""
    annotation = _fake_anno(3)
    data = {
        'parent': rt.parent_values(annotation),
        'subscription': {'id': 1}
    }

    send = rt.check_conditions(annotation, data)
    assert send is False


def test_different_subscription():
    """If subscription.uri is different from user, do not send!"""
    annotation = _fake_anno(1)
    data = {
        'parent': rt.parent_values(annotation),
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
        'parent': rt.parent_values(annotation),
        'subscription': {
            'id': 1,
            'uri': 'acct:elephant@nomouse.pls'
        }
    }

    send = rt.check_conditions(annotation, data)
    assert send is True

generate_notifications_fixtures = pytest.mark.usefixtures('effective_principals')

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
@patch('h.notification.reply_template.render_reply_notification')
@patch('h.notification.reply_template.Subscriptions')
def test_generate_notifications_only_if_author_can_read_reply(Subscriptions,
                                                              render_reply_notification,
                                                              effective_principals):
    """
    If the annotation is not readable by the parent author, no notifications
    should be generated.
    """
    private_annotation = _fake_anno(6)
    shared_annotation = _fake_anno(7)
    request = _fake_request()
    effective_principals.return_value = [
        security.Everyone,
        security.Authenticated,
        'acct:amrit@example.org',
        'group:wibble',
    ]
    Subscriptions.get_active_subscriptions_for_a_type.return_value = [
        MockSubscription(id=1, uri='acct:amrit@example.org')
    ]
    render_reply_notification.return_value = (
        'Dummy subject',
        'Dummy text',
        'Dummy HTML',
        ['dummy@example.com']
    )

    notifications = rt.generate_notifications(request, private_annotation, 'create')
    assert list(notifications) == []

    notifications = rt.generate_notifications(request, shared_annotation, 'create')
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

    Subscriptions.get_active_subscriptions_for_a_type.assert_called_with(
        REPLY_TYPE)


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
            with patch('h.notification.reply_template.render') as mock_render:
                mock_render.return_value = ''
                with patch('h.notification.reply_template.get_user_by_name') as mock_user_db:
                    user = Mock()
                    user.email = 'testmail@test.com'
                    mock_user_db.return_value = user
                    msgs = rt.generate_notifications(request, annotation, 'create')
                    msgs.next()


@pytest.fixture
def effective_principals(request):
    patcher = patch('h.auth.effective_principals')
    func = patcher.start()
    func.return_value = [security.Everyone]
    request.addfinalizer(patcher.stop)
    return func


@pytest.fixture(autouse=True)
def fetch(request):
    patcher = patch.object(storage, 'fetch_annotation')
    fetch = patcher.start()
    fetch.side_effect = _fake_anno
    request.addfinalizer(patcher.stop)
    return fetch
