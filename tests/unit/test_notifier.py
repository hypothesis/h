# -*- coding: utf-8 -*-
"""Defines unit tests for h.notifier."""
from mock import patch, Mock
from pyramid.testing import DummyRequest

from h import events, notifier
from h.streamer import FilterHandler
from . import AppTestCase


class NotifierTest(AppTestCase):
    """All Notification related unit tests live here"""
    # pylint: disable=no-self-use,too-many-public-methods

    class QueryMock(object):
        """This class is used to simulate user subscription queries"""
        # pylint: disable=too-few-public-methods

        def __init__(self, active=False, query=None, template=""):
            self.active = active
            self.query = query or {}
            self.template = template

    # Tests for handling AnnotationEvent
    def test_authorization(self):
        """Make sure private annotations don't send notifications
        """
        annotation = {'permissions': {'read': ['acct:test@example.com']}}
        request = DummyRequest()
        event = events.AnnotationEvent(request, annotation, 'create')

        with patch('h.notifier.AnnotationNotifier') as mock:
            notifier.send_notifications(event)
            assert mock.call_count == 0

    def test_passive_queries(self):
        """Make sure if a query is passive the notifier system
        does not get called"""
        annotation = {'permissions': {'read': ["group:__world__"]}}
        request = DummyRequest()
        event = events.AnnotationEvent(request, annotation, 'create')

        with patch('h.notifier.AnnotationNotifier') as mock_notif:
            with patch('h.models.UserSubscriptions.get_all') \
                    as mock_subscription:
                query = self.QueryMock()
                mock_subscription.all = Mock(return_value=[query])
                mock_notif().send_notification_to_owner = Mock()
                notifier.send_notifications(event)
                assert mock_notif().send_notification_to_owner.call_count == 0

    def test_query_matches(self):
        """Make sure that the query match triggers the notifier call"""
        annotation = {
            'permissions': {'read': ["group:__world__"]},
            'parent': {'user': 'acct:testuser@testdomain'},
            'user': 'acct:testuser@testdomain'
        }
        request = DummyRequest()
        event = events.AnnotationEvent(request, annotation, 'create')
        with patch('h.notifier.AnnotationNotifier') as mock_notif:
            with patch('h.models.UserSubscriptions') as mock_subscription:
                with patch('h.notifier.FilterHandler') as mock_filter:
                    query = self.QueryMock(active=True)
                    als = Mock()
                    als.all = Mock(return_value=[query])
                    mock_subscription.get_all = Mock(return_value=als)

                    mock_filter().match = Mock(return_value=True)
                    notifier.send_notifications(event)
                    actual = mock_notif().send_notification_to_owner.call_count
                    assert actual == 1

    def test_query_mismatch(self):
        """Make sure that the lack of matching prevents calling
        the AnnotationNotifier"""
        annotation = {
            'permissions': {'read': ["group:__world__"]},
            'parent': {'user': 'acct:testuser@testdomain'},
            'user': 'acct:testuser@testdomain'
        }
        request = DummyRequest()
        event = events.AnnotationEvent(request, annotation, 'create')
        with patch('h.notifier.AnnotationNotifier') as mock_notif:
            with patch('h.models.UserSubscriptions') as mock_subscription:
                with patch('h.notifier.FilterHandler') as mock_filter:
                    query = self.QueryMock(active=True)
                    als = Mock()
                    als.all = Mock(return_value=[query])
                    mock_subscription.get_all = Mock(return_value=als)

                    mock_filter().match = Mock(return_value=False)
                    notifier.send_notifications(event)
                    actual = mock_notif().send_notification_to_owner.call_count
                    assert actual == 0

    # Tests for AnnotationNotifier
    def test_template_registration(self):
        """Make sure the AnnotatioNotifier uses the given key and function
        for template registration"""

        def test_fn():
            """Dummy test function"""
            pass

        notifier.AnnotationNotifier.register_template('test_template', test_fn)
        templates = notifier.AnnotationNotifier.registered_templates
        assert 'test_template' in templates
        assert templates['test_template'] == test_fn

    def test_false_templates(self):
        """Make sure we do not process anything for false templates"""
        request = DummyRequest()
        notif = notifier.AnnotationNotifier(request)
        with patch.object(notif, '_send_annotation') as send:
            notif.send_notification_to_owner({}, {}, 'false_template')
            assert send.called is False

    def test_bad_status(self):
        """Make sure if a renderer throws a false status (i.e. for errors)
        then no notification is sent"""

        def test_generator(request, annotation, data):
            # pylint: disable=unused-argument
            """Our test template function, auto fails"""
            return {"status": False}

        notifier.AnnotationNotifier.register_template("test", test_generator)
        request = DummyRequest()
        notif = notifier.AnnotationNotifier(request)
        with patch.object(notif, '_send_annotation') as send:
            notif.send_notification_to_owner({}, {}, 'test')
            assert send.call_count == 0

    def test_template_parameters(self):
        """Make sure the body, subject, recipients fields are correct"""

        def test_generator(request, annotation, data):
            # pylint: disable=unused-argument
            """Our test template function"""
            return {
                "status": True,
                "rendered": "Test body",
                "subject": "Test subject",
                "recipients": ["Test user"]
            }

        notifier.AnnotationNotifier.register_template("test", test_generator)
        request = DummyRequest()
        notif = notifier.AnnotationNotifier(request)
        with patch.object(notif, '_send_annotation') as send:
            notif.send_notification_to_owner({}, {}, 'test')
            assert send.called_with('Test body', 'Test subject', ['Test user'])

    # Tests for notifier.NotificationTemplate
    def test_check_conditions(self):
        """Make sure if the check_conditions() returns False then the
        generate_notification returns with a false status"""

        class FalseTemplate(notifier.NotificationTemplate):
            """Our false template class"""
            # pylint: disable=abstract-method

            @staticmethod
            def check_conditions(annotation, data):
                """This is our false condition function"""
                return False
        result = FalseTemplate.generate_notification({}, {}, {})
        assert result['status'] is False

    def test_subject_and_recipients(self):
        """Make sure the recipients are generated by the get_recipients() and
        template, subject are generated by render()"""

        class TestTemplate(notifier.NotificationTemplate):
            """Our test template class"""
            # pylint: disable=abstract-method

            @staticmethod
            def get_recipients(request, annotation, data):
                """Our mock get_recipients function"""
                return ["test user"]

            @classmethod
            def render(cls, request, annotation):
                """Our mock render function"""
                return "test body", "test subject"

        result = TestTemplate.generate_notification({}, {}, {})
        assert result['status'] is True
        assert result['recipients'] == ['test user']
        assert result['rendered'] == 'test body'
        assert result['subject'] == 'test subject'

    # Tests for reply notifications
    def test_reply_registration(self):
        """We should have registered the ReplyTemplate.generate_notification"""
        templates = notifier.AnnotationNotifier.registered_templates
        assert 'reply_notification' in templates
        registered_fn = templates['reply_notification']
        right_fn = notifier.ReplyTemplate.generate_notification
        assert registered_fn == right_fn

    def test_reply_query_match(self):
        """Check if the generated query really matches on
        the parent annotation user"""
        annotation = {'parent': {'user': 'acct:testuser@testdomain'}}
        query = notifier.generate_system_reply_query('testuser', 'testdomain')
        assert FilterHandler(query).match(annotation, 'create') is True

    def test_reply_username_mismatch(self):
        """Check if the generated query requires the domain to match."""
        annotation = {'parent': {'user': 'acct:testuser2@testdomain'}}
        query = notifier.generate_system_reply_query('testuser', 'testdomain')
        assert FilterHandler(query).match(annotation, 'create') is False

    def test_reply_domain_mismatch(self):
        """Check if the generated query really do not match on
        any other domain"""
        annotation = {'parent': {'user': 'acct:testuser@testdomain2'}}
        query = notifier.generate_system_reply_query('testuser', 'testdomain')
        assert FilterHandler(query).match(annotation, 'create') is False

    def test_reply_ignore_root(self):
        """Don't send reply notification for a top level annotation"""
        annotation = {
            'permissions': {'read': ['group:__world__']},
            'user': 'acct:testuser@domain'
        }

        request = DummyRequest()
        with patch('h.notifier.parent_values') as mock_parent_fn:
            mock_parent_fn.return_value = {}
            annotation['parent'] = notifier.parent_values(annotation, request)
            actual = notifier.ReplyTemplate.check_conditions(annotation, {})
            assert actual is False

    def test_reply_to_self(self):
        """Don't send reply notification to yourself"""
        annotation = {
            'permissions': {'read': ['group:__world__']},
            'user': 'acct:testuser@domain'
        }

        request = DummyRequest()
        with patch('h.notifier.parent_values') as mock_parent_fn:
            mock_parent_fn.return_value = {'user': 'acct:testuser@domain'}
            annotation['parent'] = notifier.parent_values(annotation, request)
            actual = notifier.ReplyTemplate.check_conditions(annotation, {})
            assert actual is False

    def test_reply_to_other(self):
        """Send reply notification when somebody replies to you"""
        annotation = {
            'permissions': {'read': ['group:__world__']},
            'user': 'acct:testuser@domain'
        }

        request = DummyRequest()
        with patch('h.notifier.parent_values') as mock_parent_fn:
            mock_parent_fn.return_value = {'user': 'acct:testuser2@domain'}
            annotation['parent'] = notifier.parent_values(annotation, request)
            actual = notifier.ReplyTemplate.check_conditions(annotation, {})
            assert actual is True
