# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import security
from pyramid.httpexceptions import HTTPNoContent

from h.views.api_config import api_config
from h.emails import flag_notification
from h import links
from h.interfaces import IGroupService
from h.tasks import mailer


@api_config(route_name='api.annotation_flag',
            request_method='PUT',
            link_name='annotation.flag',
            description='Flag an annotation for review.',
            effective_principals=security.Authenticated,
            permission='read')
def create(context, request):
    svc = request.find_service(name='flag')
    svc.create(request.user, context.annotation)

    _email_group_admin(request, context.annotation)

    return HTTPNoContent()


def _email_group_admin(request, annotation):
    group_service = request.find_service(IGroupService)
    group = group_service.find(annotation.groupid)

    incontext_link = links.incontext_link(request, annotation)
    if incontext_link is None:
        incontext_link = annotation.target_uri

    if group.creator is not None:
        send_params = flag_notification.generate(request, group.creator.email, incontext_link)
        mailer.send.delay(*send_params)
