# -*- coding: utf-8 -*-


class AnnotationEvent(object):
    """An event representing an action on an annotation."""

    def __init__(self, request, annotation_dict, action):
        self.request = request
        self.annotation_dict = annotation_dict
        self.action = action

    @property
    def annotation_id(self):
        if self.annotation_dict:
            return self.annotation_dict.get('id')


class AnnotationBeforeSaveEvent(object):

    """
    An event fired just before an annotation is saved.

    This event can be used by subscribers who wish to modify the content of an
    annotation just before it is saved.
    """

    def __init__(self, request, annotation):
        self.request = request
        self.annotation = annotation
