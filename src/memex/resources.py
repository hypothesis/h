# -*- coding: utf-8 -*-

from memex import storage


class AnnotationFactory(object):
    def __init__(self, request):
        self.request = request

    def __getitem__(self, id):
        annotation = storage.fetch_annotation(self.request.db, id)
        if annotation is None:
            raise KeyError()
        return annotation
