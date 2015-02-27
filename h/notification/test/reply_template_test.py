# -*- coding: utf-8 -*-
"""Defines unit tests for h.notifier."""
from mock import patch, Mock, MagicMock

from pytest import raises
from pyramid.testing import DummyRequest

from h.notification.gateway import user_name, user_profile_url, standalone_url
from h.notification import reply_template as rt
from h.notification.types import REPLY_TYPE


def _create_request():
    mock_dumps = Mock(return_value='TOKEN')
    request = DummyRequest()
    request.domain = 'www.howtoreachtheark.now'
    request.registry.notification_serializer = Mock(dumps=mock_dumps)
    request.route_url = Mock()
    request.route_url.return_value = 'UNSUBSCRIBE_URL'
    return request

store_fake_data = [
    {
        # Root (parent)
        'id': '0',
        'created': '2013-10-27T19:40:53.245691+00:00',
        'document': {'title': 'How to reach the ark NOW?'},
        'text': 'The animals went in two by two, hurrah! hurrah!',
        'uri': 'www.howtoreachtheark.now',
        'user': 'acct:elephant@nomouse.pls'
    },
    {
        # Reply
        'id': '1',
        'created': '2014-10-27T19:50:53.245691+00:00',
        'document': {'title': 'How to reach the ark NOW?'},
        'text': 'The animals went in three by three, hurrah! hurrah',
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
        'references': [0],
        'uri': 'www.howtoreachtheark.now',
        'user': 'acct:elephant@nomouse.pls'
    },
    {
        # Reply to the root with the same user
        'id': '3',
        'created': '2014-10-27T20:40:53.245691+00:00',
        'document': {'title': ''},
        'text': 'The animals went in two by two, hurrah! hurrah!',
        'references': [0],
        'uri': 'www.howtoreachtheark.now',
        'user': 'acct:elephant@nomouse.pls'
    },

]


def fake_fetch(id):
    return store_fake_data[id]


# Tests for the parent_values function
def test_parent_values_reply():
    """Test if the function gives back the correct parent_value"""
    with patch('h.notification.reply_template.Annotation') as mock_annotation:
        mock_annotation.fetch = MagicMock(side_effect=fake_fetch)
        annotation = store_fake_data[1]
        parent = rt.parent_values(annotation)

        assert parent['id'] == '0'


def test_parent_values_root_annotation():
    """Test if it gives back an empty dict for root annotations"""
    with patch('h.notification.reply_template.Annotation') as mock_annotation:
        mock_annotation.fetch = MagicMock(side_effect=fake_fetch)
        annotation = store_fake_data[0]
        parent = rt.parent_values(annotation)

        assert len(parent.items()) == 0


# Tests for the create_template_map function
def test_all_keys_are_there():
    """Checks for the existence of every needed key for the template"""
    with patch('h.notification.reply_template.Annotation') as mock_annotation:
        mock_annotation.fetch = MagicMock(side_effect=fake_fetch)
        request = _create_request()
        annotation = store_fake_data[1]

        data = {
            'parent': rt.parent_values(annotation),
            'subscription': {'id': 1}
        }
        tmap = rt.create_template_map(request, annotation, data)

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
    with patch('h.notification.reply_template.Annotation') as mock_annotation:
        mock_annotation.fetch = MagicMock(side_effect=fake_fetch)
        request = _create_request()
        annotation = store_fake_data[1]

        data = {
            'parent': rt.parent_values(annotation),
            'subscription': {'id': 1}
        }
        tmap = rt.create_template_map(request, annotation, data)

        parent = store_fake_data[0]

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


def test_fallback_title():
    """Checks that the title falls back to using the url"""
    with patch('h.notification.reply_template.Annotation') as mock_annotation:
        mock_annotation.fetch = MagicMock(side_effect=fake_fetch)
        request = _create_request()
        annotation = store_fake_data[4]

        data = {
            'parent': rt.parent_values(annotation),
            'subscription': {'id': 1}
        }
        tmap = rt.create_template_map(request, annotation, data)
        assert tmap['document_title'] == annotation['uri']


def test_unsubscribe_token_generation():
    """ensures that a serialized token is generated for the unsubscribe url"""
    with patch('h.notification.reply_template.Annotation') as mock_annotation:
        mock_annotation.fetch = MagicMock(side_effect=fake_fetch)
        request = _create_request()
        annotation = store_fake_data[4]

        data = {
            'parent': rt.parent_values(annotation),
            'subscription': {'id': 1}
        }
        rt.create_template_map(request, annotation, data)

        notification_serializer = request.registry.notification_serializer
        notification_serializer.dumps.assert_called_with({
            'type': REPLY_TYPE,
            'uri': data['parent']['user'],
        })


def test_unsubscribe_url_generation():
    """ensures that a serialized token is generated for the unsubscribe url"""
    with patch('h.notification.reply_template.Annotation') as mock_annotation:
        mock_annotation.fetch = MagicMock(side_effect=fake_fetch)
        request = _create_request()
        annotation = store_fake_data[4]

        data = {
            'parent': rt.parent_values(annotation),
            'subscription': {'id': 1}
        }
        rt.create_template_map(request, annotation, data)

        request.route_url.assert_called_with('unsubscribe', token='TOKEN')

# Tests for the get_recipients function
def test_get_email():
    """Tests whether it gives back the user.email property"""
    with patch('h.notification.reply_template.Annotation') as mock_annotation:
        mock_annotation.fetch = MagicMock(side_effect=fake_fetch)
        with patch('h.notification.reply_template.get_user_by_name') as mock_user_db:
            user = Mock()
            user.email = 'testmail@test.com'
            mock_user_db.return_value = user
            request = _create_request()

            annotation = store_fake_data[1]
            data = {
                'parent': rt.parent_values(annotation),
                'subscription': {'id': 1}
            }

            email = rt.get_recipients(request, data)
            assert email[0] == user.email


def test_no_email():
    """If user has no email we must throw an exception"""
    with patch('h.notification.reply_template.Annotation') as mock_annotation:
        mock_annotation.fetch = MagicMock(side_effect=fake_fetch)
        with patch('h.notification.reply_template.get_user_by_name') as mock_user_db:
            mock_user_db.return_value = {}
            request = _create_request()

            annotation = store_fake_data[1]
            data = {
                'parent': rt.parent_values(annotation),
                'subscription': {'id': 1}
            }

            exc = False
            try:
                rt.get_recipients(request, data)
            except:
                exc = True
            assert exc


# Tests for the check_conditions function
def test_dont_send_to_the_same_user():
    """Tests that if the parent user and the annotation user is the same
    then this function returns False"""
    with patch('h.notification.reply_template.Annotation') as mock_annotation:
        mock_annotation.fetch = MagicMock(side_effect=fake_fetch)

        annotation = store_fake_data[0]
        data = {
            'parent': rt.parent_values(annotation),
            'subscription': {'id': 1}
        }

        send = rt.check_conditions(annotation, data)
        assert send is False


def test_dont_send_if_parent_is_missing():
    """Tests that this function returns False if the annotations parent's user is missing"""
    with patch('h.notification.reply_template.Annotation') as mock_annotation:
        mock_annotation.fetch = MagicMock(side_effect=fake_fetch)

        annotation = store_fake_data[3]
        data = {
            'parent': rt.parent_values(annotation),
            'subscription': {'id': 1}
        }

        send = rt.check_conditions(annotation, data)
        assert send is False


def test_different_subscription():
    """If subscription.uri is different from user, do not send!"""
    with patch('h.notification.reply_template.Annotation') as mock_annotation:
        mock_annotation.fetch = MagicMock(side_effect=fake_fetch)

        annotation = store_fake_data[1]
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
    with patch('h.notification.reply_template.Annotation') as mock_annotation:
        mock_annotation.fetch = MagicMock(side_effect=fake_fetch)

        annotation = store_fake_data[1]
        data = {
            'parent': rt.parent_values(annotation),
            'subscription': {
                'id': 1,
                'uri': 'acct:elephant@nomouse.pls'
            }
        }

        send = rt.check_conditions(annotation, data)
        assert send is True


# Tests for the generate_notifications function
def test_action_update():
    """It action is not create, it should immediately return"""
    annotation = {}
    request = DummyRequest()
    with patch('h.notification.reply_template.parent_values') as mock_parent:
        msgs = rt.generate_notifications(request, annotation, 'update')
        with raises(StopIteration):
            msgs.next()
        assert mock_parent.call_count == 0


def test_action_create():
    """If the action is create, it'll try to get the subscriptions"""
    with patch('h.notification.reply_template.Annotation') as mock_annotation:
        mock_annotation.fetch = MagicMock(side_effect=fake_fetch)
        request = _create_request()

        annotation = store_fake_data[1]
        with patch('h.notification.reply_template.Subscriptions') as mock_subs:
            mock_subs.get_active_subscriptions_for_a_type.return_value = []
            msgs = rt.generate_notifications(request, annotation, 'create')
            with raises(StopIteration):
                msgs.next()
            assert mock_subs.get_active_subscriptions_for_a_type.called


class MockSubscription(Mock):
    def __json__(self, request):
        return {
            'id': self.id or '',
            'uri': self.uri or ''
        }


def test_check_conditions_false_stops_sending():
    """If the check conditions() returns False, no notifications are generated"""
    with patch('h.notification.reply_template.Annotation') as mock_annotation:
        mock_annotation.fetch = MagicMock(side_effect=fake_fetch)
        request = _create_request()

        annotation = store_fake_data[1]
        with patch('h.notification.reply_template.Subscriptions') as mock_subs:
            mock_subs.get_active_subscriptions_for_a_type.return_value = [
                MockSubscription(id=1, uri='acct:elephant@nomouse.pls')
            ]
            with patch('h.notification.reply_template.check_conditions') as mock_conditions:
                mock_conditions.return_value = False
                with raises(StopIteration):
                    msgs = rt.generate_notifications(request, annotation, 'create')
                    msgs.next()


def test_send_if_everything_is_okay():
    """Test whether we generate notifications if every condition is okay"""
    with patch('h.notification.reply_template.Annotation') as mock_annotation:
        mock_annotation.fetch = MagicMock(side_effect=fake_fetch)
        request = _create_request()

        annotation = store_fake_data[1]
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
