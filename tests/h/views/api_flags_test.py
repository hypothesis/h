# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from pyramid.httpexceptions import HTTPNoContent, HTTPNotFound

from h.schemas import ValidationError
from h.views import api_flags as views


class FakeAnnotationResourceFactory(object):
    def __init__(self, expected_annotation):
        self.expected_annotation = expected_annotation

    def __getitem__(self, id_):
        """Return the expected annotation when the id matches, otherwise raise."""

        if id_ == self.expected_annotation.id:
            return mock.Mock(annotation=self.expected_annotation)

        raise KeyError()


@pytest.mark.usefixtures('flag_service')
class TestCreate(object):
    def test_it_flags_annotation(self,
                                 pyramid_request,
                                 annotation,
                                 flag_service):
        pyramid_request.json_body = {'annotation': annotation.id}
        context = FakeAnnotationResourceFactory(annotation)

        views.create(context, pyramid_request)

        flag_service.create.assert_called_once_with(pyramid_request.authenticated_user,
                                                    annotation)

    def test_it_returns_no_content(self, pyramid_request, annotation):
        pyramid_request.json_body = {'annotation': annotation.id}
        context = FakeAnnotationResourceFactory(annotation)

        response = views.create(context, pyramid_request)
        assert isinstance(response, HTTPNoContent)

    def test_it_raises_for_malformed_request_body(self, pyramid_request, annotation):
        type(pyramid_request).json_body = mock.PropertyMock(side_effect=ValueError('not json!'))
        context = FakeAnnotationResourceFactory(annotation)

        with pytest.raises(ValidationError):
            views.create(context, pyramid_request)

    def test_it_raises_for_missing_annotation_id(self, pyramid_request, annotation):
        pyramid_request.json_body = {}
        context = FakeAnnotationResourceFactory(annotation)

        with pytest.raises(ValidationError):
            views.create(context, pyramid_request)

    def test_it_renders_error_when_annotation_does_not_exist(self, pyramid_request, annotation):
        pyramid_request.json_body = {'annotation': 'bogus'}
        context = FakeAnnotationResourceFactory(annotation)

        with pytest.raises(HTTPNotFound) as exc:
            views.create(context, pyramid_request)

        assert 'cannot find annotation' in exc.value.message

    def test_it_renders_error_when_user_does_not_have_read_permission(self,
                                                                      pyramid_request,
                                                                      annotation):

        def fake_has_permission(action, _):
            if action == 'read':
                return False
            return True

        pyramid_request.has_permission = mock.Mock(side_effect=fake_has_permission)
        pyramid_request.json_body = {'annotation': annotation.id}
        context = FakeAnnotationResourceFactory(annotation)

        with pytest.raises(HTTPNotFound) as exc:
            views.create(context, pyramid_request)

        assert 'cannot find annotation' in exc.value.message

    @pytest.fixture
    def pyramid_request(self, pyramid_request, annotation):
        pyramid_request.authenticated_user = mock.Mock()
        pyramid_request.json_body = {}
        return pyramid_request

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation()

    @pytest.fixture
    def flag_service(self, pyramid_config):
        flag_service = mock.Mock(spec_set=['create'])
        pyramid_config.register_service(flag_service, name='flag')
        return flag_service


@pytest.mark.usefixtures('flag_service')
class TestIndex(object):
    def test_it_passes_user_filter(self, pyramid_request, flag_service):
        views.index(pyramid_request)
        flag_service.list.assert_called_once_with(pyramid_request.authenticated_user,
                                                  group=None,
                                                  uris=[])

    def test_it_passes_group_filter(self, pyramid_request, flag_service):
        pyramid_request.GET['group'] = 'test-pubid'

        views.index(pyramid_request)

        flag_service.list.assert_called_once_with(mock.ANY,
                                                  group='test-pubid',
                                                  uris=[])

    def test_it_skips_empty_group_filter(self, pyramid_request, flag_service):
        pyramid_request.GET['group'] = ''

        views.index(pyramid_request)

        flag_service.list.assert_called_once_with(mock.ANY,
                                                  group=None,
                                                  uris=[])

    def test_it_passes_uris_filter(self, pyramid_request, flag_service):
        pyramid_request.GET.add('uri', 'https://example.com/document')
        pyramid_request.GET.add('uri', 'https://example.org/document')

        views.index(pyramid_request)

        flag_service.list.assert_called_once_with(mock.ANY,
                                                  group=mock.ANY,
                                                  uris=['https://example.com/document', 'https://example.org/document'])

    def test_it_renders_flags(self, pyramid_request, flags):
        expected = [{'annotation': f.annotation_id} for f in flags]

        response = views.index(pyramid_request)
        assert response == expected

    @pytest.fixture
    def flags(self, factories):
        return [factories.Flag.build(annotation_id='test-annotation-1'),
                factories.Flag.build(annotation_id='test-annotation-2'),
                factories.Flag.build(annotation_id='test-annotation-3')]

    @pytest.fixture
    def flag_service(self, pyramid_config, flags):
        flag_service = mock.Mock(spec_set=['list'])
        flag_service.list.return_value = flags
        pyramid_config.register_service(flag_service, name='flag')
        return flag_service

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.authenticated_user = mock.Mock()
        return pyramid_request
