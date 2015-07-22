# -*- coding: utf-8 -*-

import deform
from pyramid import httpexceptions as exc
from pyramid.view import view_config

from h.groups import schemas
from h.groups import models


@view_config(route_name='group_create',
             request_method='GET',
             renderer='h:groups/templates/create_group.html.jinja2')
def create_group_form(request):
    if not request.feature('groups'):
        raise exc.HTTPNotFound()

    schema = schemas.GroupSchema().bind(request=request)
    form = deform.Form(schema)

    return {'form': form}


@view_config(route_name='group_create', request_method='POST')
def create_group(request):
    if not request.feature('groups'):
        raise exc.HTTPNotFound()

    group = models.Group(name=request.params["name"])
    request.db.add(group)

    # We need to flush the db session here so that group.id will be generated.
    request.db.flush()

    return exc.HTTPSeeOther(
        location=request.route_url('group_read', id=group.id, slug=group.slug))


@view_config(route_name='group_read',
             request_method='GET',
             renderer='h:groups/templates/read_group.html.jinja2')
def read_group(request):
    if not request.feature('groups'):
        raise exc.HTTPNotFound()

    id_ = int(request.matchdict["id"])
    group = models.Group.get_by_id(id_)
    if group is None:
        raise exc.HTTPNotFound
    return {"group": group}


def includeme(config):
    config.add_route('group_create', '/groups/new')
    config.add_route('group_read', '/groups/{id}/{slug}')
    config.scan(__name__)
