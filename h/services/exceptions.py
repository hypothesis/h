# -*- coding: utf-8 -*-

from __future__ import unicode_literals


class NotPreloadedError(Exception):
    def __init__(self, annotation_id):
        message = 'ID {} not in preloaded IDs'.format(annotation_id)
        super(NotPreloadedError, self).__init__(message)
