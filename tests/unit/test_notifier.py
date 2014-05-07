# -*- coding: utf-8 -*-
"""Unit tests for our email notifications module"""
from mock import patch, Mock
from pyramid.testing import DummyRequest

from h import events, notifier
from h.streamer import FilterHandler
from . import AppTestCase


class NotifierTest(AppTestCase): # pylint: disable=R0904
    """All Notification related unit tests live here"""
    class QueryMock(object):  # pylint: disable=R0903
        """This class is used to simulate user subscription queries"""
        def __init__(self, active=False, query={}, template=""):  # pylint: disable=W0102
            self.active = active
            self.query = query
            self.template = template

    # Tests for handling AnnotationEvent
    @classmethod
    def test_send_notifications_authorizations(cls):  # pylint: disable=C0103
        """Make sure private annotations don't send notifications
        """
        annotation = {'permissions': {'read': ['acct:test@example.com']}}
        request = DummyRequest()
        event = events.AnnotationEvent(request, annotation, 'create')

        with patch('h.notifier.AnnotationNotifier') as mock:
            notifier.send_notifications(event)
            assert mock.call_count == 0

    def test_passive_queries_do_not_get_executed(self):  # pylint: disable=C0103
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

    def test_call_notifier_if_query_matches(self):  # pylint: disable=C0103
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
                    assert mock_notif().send_notification_to_owner.call_count == 1

    def test_if_query_does_not_match_notifier_does_not_get_called(self):  # pylint: disable=C0103
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
                    assert mock_notif().send_notification_to_owner.call_count == 0

    # Tests for AnnotationNotifier
    @classmethod
    def test_template_registration(cls):
        """Make sure the AnnotatioNotifier uses the given key and function
        for template registration"""
        def test_fn():
            """Dummy test function"""
            pass
        notifier.AnnotationNotifier.register_template('test_template', test_fn)
        templates = notifier.AnnotationNotifier.registered_templates
        assert 'test_template' in templates
        assert templates['test_template'] == test_fn

    @classmethod
    def test_dont_send_data_for_false_templates(cls):  # pylint: disable=C0103
        """Make sure we do not process anything for false templates"""
        request = DummyRequest()
        notif = notifier.AnnotationNotifier(request)
        notif._send_annotation = Mock()  # pylint: disable=W0212
        notif.send_notification_to_owner({}, {}, 'false_template')
        assert notif._send_annotation.called is False  # pylint: disable=W0212

    @classmethod
    def test_do_not_send_notification_when_status_is_bad(cls):  # pylint: disable=C0103
        """Make sure if a renderer throws a false status (i.e. for errors)
        then no notification is sent"""
        def test_generator(request, annotation, data): # pylint: disable=W0613
            """Our test template function, auto fails"""
            return {"status": False}
        notifier.AnnotationNotifier.register_template("test", test_generator)
        request = DummyRequest()
        notif = notifier.AnnotationNotifier(request)
        notif._send_annotation = Mock()  # pylint: disable=W0212
        notif.send_notification_to_owner({}, {}, 'test')
        assert notif._send_annotation.call_count == 0  # pylint: disable=W0212

    @classmethod
    def test_send_annotation_is_called_with_the_right_parameters(cls):  # pylint: disable=C0103
        """Make sure the body, subject, recipients fields are correct"""
        def test_generator(request, annotation, data):  # pylint: disable=W0613
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
        notif._send_annotation = Mock()  # pylint: disable=W0212
        notif.send_notification_to_owner({}, {}, 'test')
        assert notif._send_annotation.called_with('Test body', 'Test subject', ['Test user']) # pylint: disable=W0212

    # Tests for NotificationTemplate
    ntemp = notifier.NotificationTemplate

    @classmethod
    def test_check_conditions_is_used_to_make_a_template_fail(cls):  # pylint: disable=C0103
        """Make sure if the check_conditions() returns False then the
        generate_notification returns with a false status"""
        class FalseTemplate(cls.ntemp):  # pylint: disable=R0903,W0232
            """Our false template class"""
            @classmethod
            def check_conditions(cls, annotation, data):  # pylint: disable=W0613
                """This is our false condition function"""
                return False
        assert FalseTemplate.generate_notification({}, {}, {})['status'] is False  # pylint: disable=E1101

    @classmethod
    def test_template_subject_recipients_generation(cls):  # pylint: disable=C0103
        """Make sure the recipients are generated by the get_recipients() and
        template, subject are generated by render()"""
        class TestTemplate(cls.ntemp):  # pylint: disable=R0903,W0232
            """Our test template class"""
            @staticmethod
            def get_recipients(request, annotation, data):  # pylint: disable=W0613
                """Our mock get_recipients function"""
                return ["test user"]

            @classmethod
            def render(cls, request, annotation):  # pylint: disable=W0613
                """Our mock render function"""
                return "test body", "test subject"

        result = TestTemplate.generate_notification({}, {}, {})  # pylint: disable=E1101
        assert result['status'] is True
        assert result['recipients'] == ['test user']
        assert result['rendered'] == 'test body'
        assert result['subject'] == 'test subject'

    # Tests for reply notifications
    rtemp = notifier.ReplyTemplate

    @classmethod
    def test_if_reply_notification_is_registered(cls):  # pylint: disable=C0103
        """Make sure these notifications are alive"""
        templates = notifier.AnnotationNotifier.registered_templates
        assert 'reply_notification' in templates

    def test_if_the_right_function_is_registered(self):  # pylint: disable=C0103
        """We should have registered the ReplyTemplate.generate_notification"""
        templates = notifier.AnnotationNotifier.registered_templates
        registered_fn = templates['reply_notification']
        right_fn = self.rtemp.generate_notification
        assert registered_fn == right_fn

    @classmethod
    def test_generated_reply_query_match(cls):  # pylint: disable=C0103
        """Check if the generated query really matches on
        the parent annotation user"""
        annotation = {'parent': {'user': 'acct:testuser@testdomain'}}
        query = notifier.generate_system_reply_query('testuser', 'testdomain')
        assert FilterHandler(query).match(annotation, 'create') is True

    @classmethod
    def test_generated_reply_query_dont_match_same_domain_different_user(cls):  # pylint: disable=C0103
        """Check if the generated query really do not match on any other user"""
        annotation = {'parent': {'user': 'acct:testuser2@testdomain'}}
        query = notifier.generate_system_reply_query('testuser', 'testdomain')
        assert FilterHandler(query).match(annotation, 'create') is False

    @classmethod
    def test_generated_reply_query_dont_match_same_user_different_domain(cls):  # pylint: disable=C0103
        """Check if the generated query really do not match on
        any other domain"""
        annotation = {'parent': {'user': 'acct:testuser@testdomain2'}}
        query = notifier.generate_system_reply_query('testuser', 'testdomain')
        assert FilterHandler(query).match(annotation, 'create') is False

    def test_dont_send_reply_notification_for_top_level_annotation(self):  # pylint: disable=C0103
        """Don't send reply notification for a top level annotation"""
        annotation = {
            'permissions': {'read': ['group:__world__']},
            'user': 'acct:testuser@domain'
        }

        request = DummyRequest()
        with patch('h.notifier.parent_values') as mock_parent_fn:
            mock_parent_fn.return_value = {}
            annotation['parent'] = notifier.parent_values(annotation, request)
            assert self.rtemp.check_conditions(annotation, {}) is False

    def test_dont_send_reply_notification_when_parent_user_is_the_same(self):  # pylint: disable=C0103
        """Don't send reply notification to yourself"""
        annotation = {
            'permissions': {'read': ['group:__world__']},
            'user': 'acct:testuser@domain'
        }

        request = DummyRequest()
        with patch('h.notifier.parent_values') as mock_parent_fn:
            mock_parent_fn.return_value = {'user': 'acct:testuser@domain'}
            annotation['parent'] = notifier.parent_values(annotation, request)
            assert self.rtemp.check_conditions(annotation, {}) is False

    def test_send_reply_notification_when_parent_user_is_different(self):  # pylint: disable=C0103
        """Send reply notification when somebody replies to you"""
        annotation = {
            'permissions': {'read': ['group:__world__']},
            'user': 'acct:testuser@domain'
        }

        request = DummyRequest()
        with patch('h.notifier.parent_values') as mock_parent_fn:
            mock_parent_fn.return_value = {'user': 'acct:testuser2@domain'}
            annotation['parent'] = notifier.parent_values(annotation, request)
            assert self.rtemp.check_conditions(annotation, {}) is True
