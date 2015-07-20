# -*- coding: utf-8 -*-

import deform
from pyramid import httpexceptions as exc
from pyramid.view import view_config

from h.groups import schemas


@view_config(route_name='group_create',
             request_method='GET',
             renderer='h:groups/templates/create_group.html.jinja2')
def create_group(request):
    if not request.feature('groups'):
        raise exc.HTTPNotFound()

    schema = schemas.GroupSchema().bind(request=request)
    form = deform.Form(schema)

    return {'form': form}


def includeme(config):
    config.add_route('group_create', '/groups/new')
    config.scan(__name__)
