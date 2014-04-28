# -*- coding: utf-8 -*-
from mock import patch
from pyramid.testing import DummyRequest

from h import events, notifier
from . import AppTestCase


class NotifierTest(AppTestCase):
    def test_send_notifications_authorizations(self):
        """Make sure private annotations don't send notifications"""
        annotation = {'permissions': {'read': ['acct:test@example.com']}}
        request = DummyRequest()
        event = events.AnnotationEvent(request, annotation, 'create')

        with patch('h.notifier.AnnotationNotifier') as mock:
            notifier.send_notifications(event)
            assert mock.call_count == 0
