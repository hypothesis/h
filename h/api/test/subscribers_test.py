# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mock
import pytest
from pyramid import testing

from h.api import events
from h.api import models
from h.api import subscribers


class TestIndexAnnotationEvent:

    def test_it_does_not_index_annotations_if_postgres_is_off(self):
        event = self.event('create')
        event.request.feature.return_value = False

        subscribers.index_annotation_event(event)

        assert not event.request.es.index_annotation.called

    def test_it_calls_index_annotation(self):
        event = self.event('create')
        event.request.feature.return_value = True

        subscribers.index_annotation_event(event)

        event.request.es.index_annotation.assert_called_once_with(
            event.request, event.annotation)

    def event(self, action):
        return mock.Mock(
            spec=events.AnnotationEvent(testing.DummyRequest(),
                                        mock.Mock(spec=models.Annotation()),
                                        action),
            action=action,
        )
