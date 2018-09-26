# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

import mock
import pytest

from h.presenters.annotation_searchindex import AnnotationSearchIndexPresenter
from h.services.annotation_moderation import AnnotationModerationService


@pytest.mark.usefixtures('DocumentSearchIndexPresenter', 'moderation_service', 'thread_ids')
class TestAnnotationSearchIndexPresenter(object):

    def test_asdict(self, DocumentSearchIndexPresenter, pyramid_request, thread_ids):

        annotation = mock.MagicMock(
            id='xyz123',
            created=datetime.datetime(2016, 2, 24, 18, 3, 25, 768),
            updated=datetime.datetime(2016, 2, 29, 10, 24, 5, 564),
            userid='acct:luke@hypothes.is',
            target_uri='http://example.com',
            target_uri_normalized='http://example.com/normalized',
            text='It is magical!',
            tags=['magic'],
            groupid='__world__',
            shared=True,
            target_selectors=[{'TestSelector': 'foobar'}],
            references=['referenced-id-1', 'referenced-id-2'],
            thread_ids=thread_ids,
            extra={'extra-1': 'foo', 'extra-2': 'bar'})
        DocumentSearchIndexPresenter.return_value.asdict.return_value = {'foo': 'bar'}

        annotation_dict = AnnotationSearchIndexPresenter(annotation, pyramid_request).asdict()

        assert annotation_dict == {
            'authority': 'hypothes.is',
            'id': 'xyz123',
            'created': '2016-02-24T18:03:25.000768+00:00',
            'updated': '2016-02-29T10:24:05.000564+00:00',
            'user': 'acct:luke@hypothes.is',
            'user_raw': 'acct:luke@hypothes.is',
            'uri': 'http://example.com',
            'text': 'It is magical!',
            'tags': ['magic'],
            'tags_raw': ['magic'],
            'group': '__world__',
            'shared': True,
            'target': [{'scope': ['http://example.com/normalized'],
                        'source': 'http://example.com',
                        'selector': [{'TestSelector': 'foobar'}]}],
            'document': {'foo': 'bar'},
            'references': ['referenced-id-1', 'referenced-id-2'],
            'thread_ids': thread_ids,
            'hidden': False,
        }

    def test_it_copies_target_uri_normalized_to_target_scope(self, pyramid_request):
        annotation = mock.MagicMock(
            userid='acct:luke@hypothes.is',
            target_uri_normalized='http://example.com/normalized',
            extra={})

        annotation_dict = AnnotationSearchIndexPresenter(annotation, pyramid_request).asdict()

        assert annotation_dict['target'][0]['scope'] == [
            'http://example.com/normalized']

    def test_it_marks_annotation_hidden_when_it_and_all_children_are_moderated(self,
                                                                               pyramid_request,
                                                                               moderation_service,
                                                                               thread_ids):
        annotation = mock.MagicMock(
            userid='acct:luke@hypothes.is',
            thread_ids=thread_ids)

        moderation_service.hidden.return_value = True
        moderation_service.all_hidden.return_value = thread_ids

        annotation_dict = AnnotationSearchIndexPresenter(annotation, pyramid_request).asdict()

        assert annotation_dict['hidden'] is True

    def test_it_does_not_mark_annotation_hidden_when_it_is_not_moderated(self,
                                                                         pyramid_request,
                                                                         moderation_service,
                                                                         thread_ids):
        annotation = mock.MagicMock(
            userid='acct:luke@hypothes.is',
            thread_ids=thread_ids)

        moderation_service.all_hidden.return_value = thread_ids

        annotation_dict = AnnotationSearchIndexPresenter(annotation, pyramid_request).asdict()

        assert annotation_dict['hidden'] is False

    def test_it_does_not_mark_annotation_hidden_when_children_are_not_moderated(self,
                                                                                pyramid_request,
                                                                                moderation_service,
                                                                                thread_ids):
        annotation = mock.MagicMock(
            userid='acct:luke@hypothes.is',
            thread_ids=thread_ids)

        moderation_service.all_hidden.return_value = thread_ids[1:]
        moderation_service.hidden.return_value = True

        annotation_dict = AnnotationSearchIndexPresenter(annotation, pyramid_request).asdict()

        assert annotation_dict['hidden'] is False

    def test_it_does_not_mark_annotation_hidden_when_not_moderated_and_no_replies(self, pyramid_request):
        thread_ids = []
        annotation = mock.MagicMock(
            userid='acct:luke@hypothes.is',
            thread_ids=thread_ids)

        annotation_dict = AnnotationSearchIndexPresenter(annotation, pyramid_request).asdict()

        assert annotation_dict['hidden'] is False

    def test_it_marks_annotation_hidden_when_moderated_and_no_replies(self, pyramid_request, moderation_service):
        thread_ids = []
        annotation = mock.MagicMock(userid='acct:luke@hypothes.is',
                                    thread_ids=thread_ids)

        moderation_service.hidden.return_value = True

        annotation_dict = AnnotationSearchIndexPresenter(annotation, pyramid_request).asdict()

        assert annotation_dict['hidden'] is True

    @pytest.fixture
    def DocumentSearchIndexPresenter(self, patch):
        class_ = patch('h.presenters.annotation_searchindex.DocumentSearchIndexPresenter')
        class_.return_value.asdict.return_value = {}
        return class_


@pytest.fixture
def moderation_service(pyramid_config):
    svc = mock.create_autospec(AnnotationModerationService, spec_set=True, instance=True)
    svc.all_hidden.return_value = []
    svc.hidden.return_value = False
    pyramid_config.register_service(svc, name='annotation_moderation')
    return svc


@pytest.fixture
def thread_ids():
    # Annotation reply ids are referred to as thread_ids in our code base.
    return ['thread-id-1', 'thread-id-2']
