# -*- coding: utf-8 -*-

from h.api import storage


class AnnotationFactory(object):
    def __init__(self, request):
        self.request = request

    def __getitem__(self, id):
        annotation = storage.fetch_annotation(id)
        if annotation is None:
            raise KeyError()
        return annotation
