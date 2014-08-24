# -*- coding: utf-8 -*-
__all__ = ['AnnotationEvent']


class AnnotationEvent(object):
    # pylint: disable=too-few-public-methods

    def __init__(self, request, annotation, action):
        self.request = request
        self.annotation = annotation
        self.action = action
