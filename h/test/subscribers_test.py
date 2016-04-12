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

    def test_it_gets_the_queue_writer(self, event):
        subscribers.publish_annotation_event(event)

        event.request.get_queue_writer.assert_called_once_with()

    def test_it_presents_the_annotation(self, event, presenters):
        subscribers.publish_annotation_event(event)

        presenters.AnnotationJSONPresenter.assert_called_once_with(
            event.request,
            event.annotation,
        )
        presenters.AnnotationJSONPresenter.return_value.asdict\
            .assert_called_once_with()

    def test_it_serializes_the_data(self, event, json, presenters):
        event.request.headers = {'X-Client-Id': 'client_id'}

        subscribers.publish_annotation_event(event)

        json.dumps.assert_called_once_with({
            'action': event.action,
            'annotation': presenters.AnnotationJSONPresenter
                .return_value.asdict.return_value,
            'src_client_id': 'client_id',
        })

    def test_it_publishes_the_serialized_data(self, event, json):
        subscribers.publish_annotation_event(event)

        event.request.get_queue_writer.return_value.publish\
            .assert_called_once_with(
                'annotations',
                json.dumps.return_value)

    @pytest.fixture
    def event(self):
        return mock.Mock(
            spec=events.AnnotationEvent(testing.DummyRequest(),
                                        mock.Mock(spec=models.Annotation()),
                                        'create'),
        )

    @pytest.fixture
    def json(self, patch):
        return patch('h.subscribers.json')

    @pytest.fixture
    def presenters(self, patch):
        return patch('h.subscribers.presenters')
