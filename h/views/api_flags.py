# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import security
from pyramid.httpexceptions import HTTPNoContent, HTTPNotFound

from h.schemas import ValidationError
from h.views.api import api_config


@api_config(route_name='api.flags',
            request_method='POST',
            link_name='flag.create',
            description='Flag an annotation for review.',
            effective_principals=security.Authenticated)
def create(context, request):
    annotation = _fetch_annotation(context, request)
    svc = request.find_service(name='flag')
    svc.create(request.authenticated_user, annotation)
    return HTTPNoContent()


@api_config(route_name='api.flags',
            request_method='GET',
            link_name='flag.index',
            description='List a users flagged annotations for review.',
            effective_principals=security.Authenticated)
def index(request):
    group = request.GET.get('group')
    if not group:
        group = None

    uris = request.GET.getall('uri')

    svc = request.find_service(name='flag')
    flags = svc.list(request.authenticated_user, group=group, uris=uris)
    return [{'annotation': flag.annotation_id} for flag in flags]


def _fetch_annotation(context, request):
    try:
        annotation_id = request.json_body.get('annotation')

        if not annotation_id:
            raise ValueError()
    except ValueError:
        raise ValidationError('annotation id is required')

    not_found_msg = 'cannot find annotation with id %s' % annotation_id

    try:
        resource = context[annotation_id]
        if not request.has_permission('read', resource):
            raise HTTPNotFound(not_found_msg)

        return resource.annotation
    except KeyError:
        raise HTTPNotFound(not_found_msg)
