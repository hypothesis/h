# -*- coding: utf-8 -*-
"""Defines unit tests for h.notifier."""
from mock import patch, Mock
from pyramid.testing import DummyRequest, testConfig

from h import events
from h.notification import notifier
from h.notification import types


class QueryMock(object):
    """This class is used to simulate user subscription queries"""
    # pylint: disable=too-few-public-methods

    def __init__(self, active=False, query=None, template=""):
        self.active = active
        self.query = query or {}
        self.template = template


def create_annotation(with_subscription=False):
    annotation = {
        'id': '2',
        'title': 'Example annotation',
        'quote': '',
        'text': 'this is a reply',
        'user': 'acct:testuser@testdomain',
        'permissions': {'read': ["group:__world__"]},
        'created': '2014-09-17T09:10:44.427079+00:00',
    }
    annotation_parent = {
        'uri': 'http://example.com',
        'quote': 'parent quote',
        'text': 'parent text',
        'created': '2014-09-17T09:10:44.427079+00:00',
        'user': 'acct:parent@testdomain',
        'id': '1',
    }

    parent = {'parent': annotation_parent}
    if with_subscription:
        parent['subscription'] = {
            'uri': parent['parent']['user'],
            'parameters': {},
            'query': {}
        }

    return annotation, parent

def dummy_template():
    # Dummy test functions
    def template_map(request, reply, data):
        lyrics = (
            "And so you code..."
            "And so you code..."
            "And so you code..."
            "You're at the office, everyday"
            "Typing thousands lines of code"
            "You spend your days debugging scripts"
            "And your boss gives you the creeps"
            "Sixty five Developers"
            "Planted in dark cubicles"
            "Your team is always very late"
            "Your work is just impossible"
            "The deadline is already missed"
            "CEO is always pissed"
            "You drown yourself in tones of code"
            "What a lousy daily mode"
        )
        return {
            'title': 'And So You Code',
            'lyrics': lyrics,
            'author': 'Mishu'
        }

    def recipients(request, annotation, data):
        return ['alice@wonder.land']

    def conditions(annotation, data):
        return True

    return {
        types.TEXT_PATH: 'h:dummy_test.txt',
        types.HTML_PATH: 'h:dummy_test.pt',
        types.SUBJECT_PATH: 'h:dummy_test_subject.txt',
        types.TEMPLATE_MAP: template_map,
        types.RECIPIENTS: recipients,
        types.CONDITIONS: conditions
    }


# Tests for handling AnnotationEvent
def test_authorization():
    """Make sure private annotations don't send notifications
    """
    annotation = {'permissions': {'read': ['acct:test@example.com']}}
    request = DummyRequest()
    event = events.AnnotationEvent(request, annotation, 'create')

    with patch('h.notifier.AnnotationNotifier') as mock:
        notifier.send_notifications(event)
        assert mock.call_count == 0


# Tests for AnnotationNotifier
def test_template_registration():
    """Make sure the AnnotatioNotifier uses the given key and function
    for template registration"""

    template = dummy_template()

    notifier.AnnotationNotifier.register_template('test_template', template)
    templates = notifier.AnnotationNotifier.registered_templates
    assert 'test_template' in templates
    assert templates['test_template'] == template


def test_false_templates():
    """Make sure we do not process anything for false templates"""
    request = DummyRequest()
    notif = notifier.AnnotationNotifier(request)
    with patch.object(notif, '_send_annotation') as send:
        notif.send_notification_to_owner({}, {}, 'false_template')
        assert send.called is False


def test_bad_status():
    """Make sure if a renderer throws a false status (i.e. for errors)
    then no notification is sent"""

    def test_generator(request, annotation, data):
        # pylint: disable=unused-argument
        """Our test template function, auto fails"""
        return {"status": False}

    template = dummy_template()
    template[types.TEMPLATE_MAP] = test_generator

    notifier.AnnotationNotifier.register_template("test", template)
    request = DummyRequest()
    notif = notifier.AnnotationNotifier(request)
    with patch.object(notif, '_send_annotation') as send:
        notif.send_notification_to_owner({}, {}, 'test')
        assert send.call_count == 0


def test_template_parameters():
    """Make sure the body, html, subject, recipients fields are correct"""

    def test_generator(request, annotation, data):
        # pylint: disable=unused-argument
        """Our test template function"""
        return {
            "status": True,
            "text": "Test body",
            "html": "Test html",
            "subject": "Test subject",
            "recipients": ["Test user"]
        }

    template = dummy_template()
    template[types.TEMPLATE_MAP] = test_generator

    notifier.AnnotationNotifier.register_template("test", template)
    request = DummyRequest()
    notif = notifier.AnnotationNotifier(request)
    with patch.object(notif, '_send_annotation') as send:
        notif.send_notification_to_owner({}, {}, 'test')
        assert send.called_with('Test body', 'Test subject', ['Test user'])


# Tests for notifier.NotificationTemplate
def test_check_conditions():
    """Make sure if the check_conditions() returns False then the
    generate_notification returns with a false status"""

    def check_conditions(annotation, data):
        """This is our false condition function"""
        return False
    template = dummy_template()
    template[types.CONDITIONS] = check_conditions

    request = DummyRequest()
    result = notifier.generate_notification(template, request, {}, {})
    assert result['status'] is False


def test_subject_and_recipients():
    """Make sure the recipients are generated by the get_recipients() and
    template, subject are generated by render()"""

    def get_recipients(request, annotation, data):
        """Our mock get_recipients function"""
        return ["test user"]

    template = dummy_template()
    template[types.RECIPIENTS] = get_recipients

    request = DummyRequest()
    with patch('h.notification.notifier.render_template') as mock_render:
        mock_render.return_value = "test subject", "test body", "test html"

        result = notifier.generate_notification(template, request, {}, {})
        assert result['status'] is True
        assert result['recipients'] == ['test user']
        assert result['text'] == 'test body'
        assert result['html'] == 'test html'
        assert result['subject'] == 'test subject'


# Tests for reply notifications
from h.notification import reply_template


def get_reply_template():
    templates = notifier.AnnotationNotifier.registered_templates
    return templates[types.REPLY_TEMPLATE]

def test_reply_registration():
    """We should have registered the ReplyTemplate.generate_notification"""
    templates = notifier.AnnotationNotifier.registered_templates
    assert types.REPLY_TEMPLATE in templates.keys()
    registered_fns = templates[types.REPLY_TEMPLATE]
    assert registered_fns[types.TEMPLATE_MAP] == reply_template.create_template_map
    assert registered_fns[types.RECIPIENTS] == reply_template.get_recipients
    assert registered_fns[types.CONDITIONS] == reply_template.check_conditions


def test_reply_query_match():
    """Test if the notifier.send_notifications is called
    """
    annotation = {
        'user': 'acct:testuser@testdomain',
        'permissions': {'read': ["group:__world__"]}
    }
    request = DummyRequest()
    event = events.AnnotationEvent(request, annotation, 'create')

    with patch('h.notification.notifier.AnnotationNotifier') as mock_notif:
        with patch('h.notification.notifier.parent_values') as mock_parent:
            with patch('h.notification.notifier.Subscriptions.get_active_subscriptions') as mock_subs:
                mock_subs.return_value = [
                    Mock(uri='acct:parent@testdomain',
                         template=types.REPLY_TEMPLATE)
                ]
                mock_parent.return_value = {'user': 'acct:parent@testdomain'}
                notifier.send_notifications(event)
                assert mock_notif().send_notification_to_owner.call_count == 1


def test_reply_notification_content():
    """
    The reply notification should have a subject, and both plain and
    html bodies.
    """
    with testConfig() as config:
        config.include('pyramid_jinja2')
        config.add_jinja2_renderer('.txt')
        config.add_jinja2_renderer('.html')

        annotation, parent = create_annotation(True)
        request = DummyRequest()

        with patch('h.auth.local.models.User') as mock_user:
            user = Mock(email='acct:parent@testdomain')
            mock_user.get_by_username.return_value = user

            notification = notifier.generate_notification(
                get_reply_template(), request, annotation, parent)

            assert notification['status']
            assert notification['recipients'] == ['acct:parent@testdomain']
            assert 'testuser has just left a reply to your annotation on' in \
                notification['text']
            assert '<a href="http://example.com/u/testuser">testuser</a> '\
                'has just left a reply to your annotation on' \
                in notification['html']
            assert notification['subject'] == \
                'testuser has replied to your annotation'


def test_reply_notification_no_recipient():
    """
    The reply notification should have a False status if the recipient cannot
    be found in the User table.
    """
    with testConfig() as config:
        config.include('pyramid_jinja2')
        config.add_jinja2_renderer('.txt')
        config.add_jinja2_renderer('.html')

        annotation, parent = create_annotation(True)
        request = DummyRequest()

        with patch('h.auth.local.models.User') as mock_user:
            with patch('h.notification.notifier.Subscriptions.get_active_subscriptions') as mock_subs:
                mock_subs.return_value = [
                    Mock(uri=parent['parent']['user'],
                         template=types.REPLY_TEMPLATE)
                ]
                mock_user.get_by_username.return_value = None

                notification = notifier.generate_notification(
                    get_reply_template(), request, annotation, parent)

                assert notification['status'] is False


def test_reply_same_creator():
    """Username same, domain same -> should not send reply"""
    annotation = {
        'user': 'acct:testuser@testdomain',
        'permissions': {'read': ["group:__world__"]}
    }
    request = DummyRequest()
    event = events.AnnotationEvent(request, annotation, 'create')

    with patch('h.notifier.AnnotationNotifier') as mock_notif:
        with patch('h.notifier.parent_values') as mock_parent:
            with patch('h.notification.notifier.Subscriptions.get_active_subscriptions') as mock_subs:
                mock_subs.return_value = [
                    Mock(uri='acct:testuser@testdomain',
                         template=types.REPLY_TEMPLATE)
                ]
                mock_parent.return_value = {'user': 'acct:testuser@testdomain'}
                notifier.send_notifications(event)
                assert mock_notif().send_notification_to_owner.call_count == 0


def test_no_parent_user():
    """Should not throw or send annotation if the parent user is missing"""
    annotation = {
        'user': 'acct:testuser@testdomain',
        'permissions': {'read': ["group:__world__"]}
    }
    request = DummyRequest()
    event = events.AnnotationEvent(request, annotation, 'create')

    with patch('h.notifier.AnnotationNotifier') as mock_notif:
        with patch('h.notifier.parent_values') as mock_parent:
            with patch('h.notification.notifier.Subscriptions.get_active_subscriptions') as mock_subs:
                mock_subs.return_value = [
                    Mock(uri='acct:testuse2r@testdomain',
                         template=types.REPLY_TEMPLATE)
                ]
                mock_parent.return_value = {}
                notifier.send_notifications(event)
                assert mock_notif().send_notification_to_owner.call_count == 0


def test_reply_update():
    """Should not do anything if the action is update"""
    annotation = {
        'user': 'acct:testuser@testdomain',
        'permissions': {'read': ["group:__world__"]}
    }
    request = DummyRequest()
    event = events.AnnotationEvent(request, annotation, 'update')

    with patch('h.notifier.AnnotationNotifier') as mock_notif:
        with patch('h.notifier.parent_values') as mock_parent:
            mock_parent.return_value = {}
            notifier.send_notifications(event)
            assert mock_notif().send_notification_to_owner.call_count == 0
