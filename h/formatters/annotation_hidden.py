# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from zope.interface import implementer

from h.formatters.interfaces import IAnnotationFormatter


@implementer(IAnnotationFormatter)
class AnnotationHiddenFormatter(object):
    """
    Formatter for dealing with annotations that a moderator has hidden.

    Any user who has permission to moderate a group will always be able to see
    whether annotations in a group have been hidden, and will be able to see
    the content of those annotations. In the unlikely event that these
    annotations are their own, they'll still be able to see them.

    Moderators aside, users are never shown that their own annotations have
    been hidden. They are always given a `False` value for the `hidden` flag.

    For any other users, if an annotation has been hidden it is presented with
    the `hidden` flag set to `True`, and the annotation's content is redacted.
    """

    def __init__(self, moderation_svc, moderator_check, user):
        self._moderation_svc = moderation_svc
        self._moderator_check = moderator_check
        self._user = user

    def format(self, annotation_resource):
        annotation = annotation_resource.annotation
        group = annotation_resource.group

        if self._current_user_is_moderator(group):
            return {'hidden': self._is_hidden(annotation)}

        if self._current_user_is_author(annotation):
            return {'hidden': False}

        if self._is_hidden(annotation):
            return {'hidden': True, 'text': '', 'tags': []}
        else:
            return {'hidden': False}

    def _current_user_is_moderator(self, group):
        return self._moderator_check(group)

    def _current_user_is_author(self, annotation):
        return self._user and self._user.userid == annotation.userid

    def _is_hidden(self, annotation):
        return self._moderation_svc.hidden(annotation)
