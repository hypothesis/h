# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h import presenters


class AnnotationJSONPresentationService(object):
    def present(self, annotation_resource):
        presenter = presenters.AnnotationJSONPresenter(annotation_resource)
        return presenter.asdict()


def annotation_json_presentation_service_factory(context, request):
    return AnnotationJSONPresentationService()
