# -*- coding: utf-8 -*-

from pyramid.view import view_config, view_defaults

from h import form  # noqa F401
from h import i18n
from h import models
from h import paginator
from h.schemas.admin_group import CreateAdminGroupSchema

_ = i18n.TranslationString


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
        self.schema = CreateAdminGroupSchema().bind(request=request)
        self.form = request.create_form(self.schema,
                                        buttons=(_('Create New Group'),))

    @view_config(request_method='GET')
    def get(self):
        self.form.set_appstruct({
            'authority': self.request.authority,
        })
        return self._template_context()

    def _template_context(self):
        return {'form': self.form.render()}
