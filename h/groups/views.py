# -*- coding: utf-8 -*-

import deform
import colander
from pyramid import httpexceptions as exc
from pyramid.view import view_config

from h.groups import schemas
from h.groups import models
from h.accounts import models as accounts_models
from h import hashids


@view_config(route_name='group_create',
             request_method='GET',
             renderer='h:groups/templates/create_group.html.jinja2',
             permission="authenticated")
def create_group_form(request):
    if not request.feature('groups'):
        raise exc.HTTPNotFound()

    schema = schemas.GroupSchema().bind(request=request)
    form = deform.Form(schema)

    return {'form': form, 'data': {}}


@view_config(route_name='group_create',
             request_method='POST',
             renderer='h:groups/templates/create_group.html.jinja2',
             permission="authenticated")
def create_group(request):
    if not request.feature('groups'):
        raise exc.HTTPNotFound()

    form = deform.Form(schemas.GroupSchema().bind(request=request))
    try:
        appstruct = form.validate(request.POST.items())
    except deform.ValidationFailure as err:
        return {'form': form, 'data': request.params}

    user = accounts_models.User.get_by_id(
        request, request.authenticated_userid)
    group = models.Group(name=appstruct["name"], creator=user)
    request.db.add(group)

    # We need to flush the db session here so that group.id will be generated.
    request.db.flush()

    hashid = hashids.encode(request, "h.groups", group.id)
    return exc.HTTPSeeOther(
        location=request.route_url(
            'group_read', hashid=hashid, slug=group.slug))


@view_config(route_name='group_read_no_slug',
             request_method='GET',
             renderer='h:groups/templates/read_group.html.jinja2')
@view_config(route_name='group_read_no_slug_trailing_slash',
             request_method='GET',
             renderer='h:groups/templates/read_group.html.jinja2')
@view_config(route_name='group_read',
             request_method='GET',
             renderer='h:groups/templates/read_group.html.jinja2')
def read_group(request):
    if not request.feature('groups'):
        raise exc.HTTPNotFound()

    hashid = request.matchdict["hashid"]
    group_id = hashids.decode(request, "h.groups", hashid)

    group = models.Group.get_by_id(group_id)
    if group is None:
        raise exc.HTTPNotFound

    # /groups/<hashid> redirects to /groups/<hashid>/<slug>.
    if "slug" not in request.matchdict:
        return exc.HTTPSeeOther(
            location=request.route_url(
                'group_read', hashid=hashid, slug=group.slug))

    return {"group": group}


def includeme(config):
    assert config.registry.settings.get("h.hashids.salt"), (
        "There needs to be a h.hashids.salt config setting")
    config.add_route('group_create', '/groups/new')
    config.add_route('group_read', '/groups/{hashid}/{slug}')
    config.add_route('group_read_no_slug', '/groups/{hashid}')
    config.add_route('group_read_no_slug_trailing_slash', '/groups/{hashid}/')
    config.scan(__name__)
