# -*- coding: utf-8 -*-

from pyramid.view import view_config, view_defaults

from h import models
from h import paginator


@view_config(route_name='admin_groups',
             request_method='GET',
             renderer='h:templates/admin/groups.html.jinja2',
             permission='admin_groups')
@paginator.paginate_query
def groups_index(context, request):
    return request.db.query(models.Group).order_by(models.Group.created.desc())


@view_defaults(route_name='admin_groups_create',
               renderer='h:templates/admin/groups_create.html.jinja2',
               permission='admin_groups')
class GroupCreateController(object):

    def __init__(self, request):
        self.request = request

    @view_config(request_method='GET')
    def get(self):
        # self.form.set_appstruct({
        #     'authority': self.request.authority,
        #     'grant_type': GrantType.authorization_code,
        #     'response_type': ResponseType.code,
        #     'trusted': False,
        # })
        return self._template_context()

    def _template_context(self):
        return {'foo': 'bar'}
