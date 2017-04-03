# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import security
from pyramid.httpexceptions import HTTPNoContent, HTTPNotFound

from h.views.api import api_config


@api_config(route_name='api.annotation_hide',
            request_method='PUT',
            link_name='annotation.hide',
            description='Hide an annotation as a group moderator.',
            effective_principals=security.Authenticated)
def create(context, request):
    if not request.has_permission('admin', context.group):
        raise HTTPNotFound()

    svc = request.find_service(name='annotation_moderation')
    svc.hide(context.annotation)
    return HTTPNoContent()
