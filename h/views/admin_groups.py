# -*- coding: utf-8 -*-

from pyramid.view import view_config

from h import models
from h import paginator


@view_config(route_name='admin_groups',
             request_method='GET',
             renderer='h:templates/admin/groups.html.jinja2',
             permission='admin_groups')
@paginator.paginate_query
def groups_index(context, request):
    return request.db.query(models.Group).order_by(models.Group.created.desc())


@view_config(route_name='admin_groups_create',
             request_method='GET',
             renderer='h:templates/admin/groups_create.html.jinja2',
             permission='admin_groups')
def groups_create(context, request):
    return []
