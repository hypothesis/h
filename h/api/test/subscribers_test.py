# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mock
import pytest
from pyramid import testing

from h.api import events
from h.api import models
from h.api import subscribers


@pytest.mark.usefixtures('index', 'delete')
class TestIndexAnnotationEvent:

    def test_it_does_not_create_annotations_if_postgres_is_off(self, index):
        event = self.event('create')
        event.request.feature.return_value = False

        subscribers.index_annotation_event(event)

        assert not index.called

    def test_it_does_not_delete_annotations_if_postgres_is_off(self, delete):
        event = self.event('delete')
        event.request.feature.return_value = False

        subscribers.index_annotation_event(event)

        assert not delete.called

    def test_it_calls_index_when_action_is_create(self, index, delete):
        event = self.event('create')
        event.request.feature.return_value = True

        subscribers.index_annotation_event(event)

        index.assert_called_once_with(
            event.request.es, event.annotation, event.request)
        assert not delete.called

    def test_it_calls_delete_when_action_is_delete(self, delete, index):
        event = self.event('delete')
        event.request.feature.return_value = True

        subscribers.index_annotation_event(event)

        delete.assert_called_once_with(event.request.es, event.annotation)
        assert not index.called

    def event(self, action):
        return mock.Mock(
            spec=events.AnnotationEvent(testing.DummyRequest(),
                                        mock.Mock(spec=models.Annotation()),
                                        action),
            action=action,
        )

    @pytest.fixture
    def index(self, patch):
        return patch('h.api.subscribers.index')

    @pytest.fixture
    def delete(self, patch):
        return patch('h.api.subscribers.delete')
