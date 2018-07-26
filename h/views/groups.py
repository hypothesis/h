# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import deform
from pyramid import httpexceptions
from pyramid import security
from pyramid.view import view_config, view_defaults

from h import form
from h import i18n
from h.groups import schemas

_ = i18n.TranslationString


@view_defaults(route_name='group_create',
               renderer='h:templates/groups/create.html.jinja2',
               effective_principals=security.Authenticated)
class GroupCreateController(object):
    def __init__(self, request):
        self.request = request

        self.schema = schemas.group_schema(autofocus_name=True).bind(
            request=self.request)

        submit = deform.Button(title=_('Create a new group'),
                               css_class='primary-action-btn '
                                         'group-form__submit-btn '
                                         'js-create-group-create-btn')
        self.form = request.create_form(self.schema,
                                        css_class='group-form__form',
                                        buttons=(submit,))

    @view_config(request_method='GET')
    def get(self):
        """Render the form for creating a new group."""
        return self._template_data()

    @view_config(request_method='POST')
    def post(self):
        """Respond to a submission of the create group form."""
        def on_success(appstruct):
            groups_service = self.request.find_service(name='group')
            group = groups_service.create_private_group(
                name=appstruct['name'],
                description=appstruct.get('description'),
                userid=self.request.authenticated_userid)

            url = self.request.route_path('group_read',
                                          pubid=group.pubid,
                                          slug=group.slug)
            return httpexceptions.HTTPSeeOther(url)

        return form.handle_form_submission(
            self.request,
            self.form,
            on_success=on_success,
            on_failure=self._template_data)

    def _template_data(self):
        """Return the data needed to render this controller's page."""
        return {'form': self.form.render()}


@view_defaults(route_name='group_edit',
               renderer='h:templates/groups/edit.html.jinja2',
               permission='admin')
class GroupEditController(object):
    def __init__(self, group, request):
        self.group = group
        self.request = request
        self.schema = schemas.group_schema().bind(request=self.request)
        self.form = request.create_form(self.schema,
                                        buttons=(_('Save'),),
                                        use_inline_editing=True)

    @view_config(request_method='GET')
    def get(self):
        self.form.set_appstruct({
            'name': self.group.name or '',
            'description': self.group.description or '',
        })

        return self._template_data()

    @view_config(request_method='POST')
    def post(self):
        return form.handle_form_submission(
                self.request,
                self.form,
                on_success=self._update_group,
                on_failure=self._template_data)

    def _template_data(self):
        return {
            'form': self.form.render(),
            'group_path': self.request.route_path('group_read',
                                                  pubid=self.group.pubid,
                                                  slug=self.group.slug)
        }

    def _update_group(self, appstruct):
        self.group.name = appstruct['name']
        self.group.description = appstruct['description']


@view_config(route_name='group_read_noslug', request_method='GET')
def read_noslug(group, request):
    check_slug(group, request)


def check_slug(group, request):
    """Redirect if the request slug does not match that of the group."""
    slug = request.matchdict.get('slug')
    if slug is None or slug != group.slug:
        path = request.route_path('group_read', pubid=group.pubid, slug=group.slug)
        raise httpexceptions.HTTPMovedPermanently(path)
