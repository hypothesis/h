# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import security
from pyramid.httpexceptions import HTTPNoContent

from h.views.api import api_config


@api_config(route_name='api.annotation_flag',
            request_method='PUT',
            link_name='annotation.flag',
            description='Flag an annotation for review.',
            effective_principals=security.Authenticated,
            permission='read')
def create(context, request):
    svc = request.find_service(name='flag')
    svc.create(request.user, context.annotation)
    return HTTPNoContent()
