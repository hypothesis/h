# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mock
import pytest
from pyramid import testing

from h import subscribers
from h.api import events
from h.api import models


@pytest.mark.usefixtures('json', 'presenters')
class TestPublishAnnotationEvent:

    def test_it_gets_the_queue_writer(self):
        event = self.event()

        subscribers.publish_annotation_event(event)

        event.request.get_queue_writer.assert_called_once_with()

    def test_it_presents_the_annotation(self):
        event = self.event()

        subscribers.publish_annotation_event(event)

        subscribers.presenters.AnnotationJSONPresenter.assert_called_once_with(
            event.request,
            event.annotation,
        )
        subscribers.presenters.AnnotationJSONPresenter.return_value.asdict\
            .assert_called_once_with()

    def test_it_serializes_the_data(self):
        event = self.event()
        event.request.headers = {'X-Client-Id': 'client_id'}

        subscribers.publish_annotation_event(event)

        subscribers.json.dumps.assert_called_once_with({
            'action': event.action,
            'annotation': subscribers.presenters.AnnotationJSONPresenter
                .return_value.asdict.return_value,
            'src_client_id': 'client_id',
        })

    def test_it_publishes_the_serialized_data(self):
        event = self.event()

        subscribers.publish_annotation_event(event)

        event.request.get_queue_writer.return_value.publish\
            .assert_called_once_with(
                'annotations',
                subscribers.json.dumps.return_value)

    def event(self):
        return mock.Mock(
            spec=events.AnnotationEvent(testing.DummyRequest(),
                                        mock.Mock(spec=models.Annotation()),
                                        'create'),
        )

    @pytest.fixture
    def json(self, monkeypatch):
        monkeypatch.setattr(
            'h.subscribers.json',
            mock.Mock(spec=subscribers.json),
        )

    @pytest.fixture
    def presenters(self, monkeypatch):
        monkeypatch.setattr(
            'h.subscribers.presenters',
            mock.Mock(spec=subscribers.presenters),
        )
