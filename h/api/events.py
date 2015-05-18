# -*- coding: utf-8 -*-
class AnnotationEvent(object):
    """An event representing an action on an annotation."""

    def __init__(self, request, annotation, action):
        self.request = request
        self.annotation = annotation
        self.action = action
