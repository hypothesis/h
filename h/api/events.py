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


class AnnotationTransformEvent(object):

    """
    An event fired before an annotation is indexed or otherwise needs to be
    transformed by third-party code.

    This event can be used by subscribers who wish to modify the content of an
    annotation just before it is indexed or in other use-cases.
    """

    def __init__(self, request, annotation_dict):
        self.request = request
        self.annotation_dict = annotation_dict
