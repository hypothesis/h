# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h.services.annotation_json_presentation import AnnotationJSONPresentationService
from h.services.annotation_json_presentation import annotation_json_presentation_service_factory


class TestAnnotationJSONPresentationService(object):
    def test_present_inits_presenter(self, svc, presenters):
        resource = mock.Mock()

        svc.present(resource)

        presenters.AnnotationJSONPresenter.assert_called_once_with(resource)

    def test_present_returns_presenter_dict(self, svc, presenters):
        presenter = presenters.AnnotationJSONPresenter.return_value

        result = svc.present(mock.Mock())

        assert result == presenter.asdict.return_value

    @pytest.fixture
    def svc(self):
        return AnnotationJSONPresentationService()

    @pytest.fixture
    def presenters(self, patch):
        return patch('h.services.annotation_json_presentation.presenters')


class TestAnnotationJSONPresentationServiceFactory(object):
    def test_returns_service(self, pyramid_request):
        svc = annotation_json_presentation_service_factory(None, pyramid_request)

        assert isinstance(svc, AnnotationJSONPresentationService)
