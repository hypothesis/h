# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
Annotation authorization.

This module provides default-permissive group authorization methods that can
be overriden by the application.
"""

GROUP_WRITE_PERMITTED_KEY = 'memex.auth.group_write_permitted'


def group_write_permitted(request, groupid):
    """
    Returns if the current request is allowed to write to the specified group.

    :param request: the request
    :type request: pyramid.request.Request

    :param groupid: the groupid
    :type groupid: unicode

    :returns: a boolean for allowing or disallowing the write
    :rtype: bool
    """
    return True


def includeme(config):
    def set_write_permitted(config, func):
        config.registry[GROUP_WRITE_PERMITTED_KEY] = func
    config.add_directive('set_memex_group_write_permitted', set_write_permitted)
