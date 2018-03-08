# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import jinja2

from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPFound

from h import form  # noqa F401
from h import i18n
from h import models
from h import paginator
from h.schemas.admin_group import CreateAdminGroupSchema
from h.interfaces import IGroupService

_ = i18n.TranslationString


class GroupNotFoundError(Exception):
    pass


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
            'creator': self.request.user.username,
        })
        return self._template_context()

    @view_config(request_method='POST')
    def post(self):
        def on_success(appstruct):
            read_url = self.request.route_url('admin_groups')
            self.request.session.flash('TODO: I will add a {gtype} group called "{name}"'
                                       ' for authority {authority}, created by {creator}'.format(
                                            gtype=appstruct['group_type'],
                                            name=appstruct['name'],
                                            authority=appstruct['authority'],
                                            creator=appstruct['creator']
                                       ), queue='success')
            response = HTTPFound(location=read_url)
            return response

        return form.handle_form_submission(self.request, self.form,
                                           on_success=on_success,
                                           on_failure=self._template_context)

    def _template_context(self):
        return {'form': self.form.render()}


@view_defaults(route_name='admin_groups_edit',
               permission='admin_groups')
class GroupEditController(object):

    def __init__(self, request):
        self.request = request

    @view_config(request_method='POST',
                 request_param='delete')
    def delete(self):
        """Process submitted delete-group form"""
        group = _form_request_group(self.request)

        self.request.session.flash('Group "{name}" will be deleted'.format(name=group.name), 'success')
        return HTTPFound(location=self.request.route_path('admin_groups'))


@view_config(context=GroupNotFoundError)
def group_not_found(exc, request):
    request.session.flash(jinja2.Markup(_(exc.message)), 'error')
    return HTTPFound(location=request.route_path('admin_groups'))


def _form_request_group(request):
    """Return the Group which a group admin form action relates to."""
    groupid = request.params.get('groupid')
    group_service = request.find_service(IGroupService)
    group = group_service.find(groupid)

    if group is None:
        raise GroupNotFoundError(_('Could not find group with pubid {pubid}'.format(pubid=groupid)))

    return group
