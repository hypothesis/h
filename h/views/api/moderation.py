# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid.httpexceptions import HTTPNoContent

from h import events
from h.views.api.config import api_config


@api_config(
    versions=["v1", "v2"],
    route_name="api.annotation_hide",
    request_method="PUT",
    link_name="annotation.hide",
    description="Hide an annotation as a group moderator",
    permission="moderate",
)
def create(context, request):

    svc = request.find_service(name="annotation_moderation")
    svc.hide(context.annotation)

    event = events.AnnotationEvent(request, context.annotation.id, "update")
    request.notify_after_commit(event)

    return HTTPNoContent()


@api_config(
    versions=["v1", "v2"],
    route_name="api.annotation_hide",
    request_method="DELETE",
    link_name="annotation.unhide",
    description="Unhide an annotation as a group moderator",
    permission="moderate",
)
def delete(context, request):

    svc = request.find_service(name="annotation_moderation")
    svc.unhide(context.annotation)

    event = events.AnnotationEvent(request, context.annotation.id, "update")
    request.notify_after_commit(event)

    return HTTPNoContent()
