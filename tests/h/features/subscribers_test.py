# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from mock import patch

from pyramid.registry import Registry
from pyramid.events import ApplicationCreated, NewRequest

from h.features.subscribers import preload_flags, remove_old_flags


class TestPreloadFlags(object):
    def test_preloads_feature_flags(self, pyramid_request):
        event = NewRequest(pyramid_request)

        preload_flags(event)

        assert event.request.feature.loaded


class TestRemoveOldFlags(object):
    def test_removes_flags(self, patch):
        db = patch('h.features.subscribers.db')
        Feature = patch('h.features.subscribers.Feature')
        event = ApplicationCreated(DummyApp())

        remove_old_flags(event)

        Feature.remove_old_flags.assert_called_once_with(db.Session.return_value)

    def test_cleans_up_database_session_and_connection(self, patch):
        db = patch('h.features.subscribers.db')
        patch('h.features.subscribers.Feature')
        event = ApplicationCreated(DummyApp())

        remove_old_flags(event)

        db.Session.return_value.close.assert_called_once_with()
        db.make_engine.return_value.dispose.assert_called_once_with()

    @patch.dict('os.environ', {'H_SCRIPT': '1'})
    def test_does_nothing_when_in_script(self, patch):
        patch('h.features.subscribers.db')
        Feature = patch('h.features.subscribers.Feature')
        event = ApplicationCreated(DummyApp())

        remove_old_flags(event)

        assert not Feature.remove_old_flags.called


class DummyApp(object):
    def __init__(self):
        self.registry = Registry('testing')
        self.registry.settings = {'sqlalchemy.url': 'sqlite:///:memory:'}
