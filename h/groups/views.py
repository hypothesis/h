# -*- coding: utf-8 -*-

import deform
from pyramid import httpexceptions as exc
from pyramid.view import view_config
from pyramid import renderers

from h.groups import schemas
from h.groups import models
from h.accounts import models as accounts_models
from h import hashids


def _url_for_group(request, group):
    """Return the URL for the given group's page."""
    hashid = hashids.encode(request, "h.groups", group.id)
    return request.route_url('group_read', hashid=hashid, slug=group.slug)


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
    except deform.ValidationFailure:
        return {'form': form, 'data': request.params}

    user = accounts_models.User.get_by_id(
        request, request.authenticated_userid)
    group = models.Group(name=appstruct["name"], creator=user)
    request.db.add(group)

    # We need to flush the db session here so that group.id will be generated.
    request.db.flush()

    return exc.HTTPSeeOther(_url_for_group(request, group))


@view_config(route_name='group_read', request_method='GET')
@view_config(route_name='group_read_noslug', request_method='GET')
def read_group(request):
    if not request.feature('groups'):
        raise exc.HTTPNotFound()

    hashid = request.matchdict["hashid"]
    slug = request.matchdict.get("slug")
    group_id = hashids.decode(request, "h.groups", hashid)

    group = models.Group.get_by_id(group_id)
    if group is None:
        raise exc.HTTPNotFound()

    if slug is None or slug != group.slug:
        return exc.HTTPMovedPermanently(
            location=_url_for_group(request, group))

    template_data = {"group": group}
    if not request.authenticated_userid:
        renderer = 'h:groups/templates/login_to_join_group.html.jinja2'
        template_data["redirect"] = _url_for_group(request, group)
    else:
        user = accounts_models.User.get_by_id(
            request, request.authenticated_userid)
        if group in user.groups:
            template_data["group_url"] = _url_for_group(request, group)
            renderer = 'h:groups/templates/read_group.html.jinja2'
        else:
            hashid = hashids.encode(request, "h.groups", group.id)
            template_data['join_url'] = request.route_url(
                'group_join', hashid=hashid, slug=group.slug)
            renderer = 'h:groups/templates/join_group.html.jinja2'

    request.response.content_type = 'text/html'
    request.response.text = renderers.render(
        renderer, template_data, request=request)
    return request.response


@view_config(route_name='group_join',
             request_method='GET',
             renderer='h:groups/templates/read_group.html.jinja2',
             permission='authenticated')
def join_group(request):
    pass


def includeme(config):
    assert config.registry.settings.get("h.hashids.salt"), (
        "There needs to be a h.hashids.salt config setting")
    config.add_route('group_create', '/groups/new')
    # Match "/groups/<hashid>/": we redirect to the version with the slug.
    config.add_route('group_read', '/groups/{hashid}/{slug:[^/]*}')
    config.add_route('group_read_noslug', '/groups/{hashid}')
    config.add_route('group_join', '/groups/{hashid}/{slug}/join')
    config.scan(__name__)
