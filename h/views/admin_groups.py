# -*- coding: utf-8 -*-
import deform

from pyramid import httpexceptions
from pyramid import security
from pyramid.config import not_
from pyramid.view import view_config, view_defaults

from h import form
from h import i18n
from h import models
from h import paginator
from h.groups import schemas

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
               permission='admin_groups',
               effective_principals=security.Authenticated)
class AdminGroupCreateController(object):
    """
    Controller for feature that lets user create a new group
    """

    def __init__(self, request):
        self.request = request

        self.schema = schemas.admin_group_create_schema().bind(
            request=self.request)

        submit = deform.Button(title=_('Create a new group'),
                               css_class='primary-action-btn '
                                         'admin-group-create-form__submit-btn '
                                         'js-create-group-create-btn')
        self.form = request.create_form(self.schema,
                                        formid='admin-group-create-form',
                                        css_class='admin-group-create-form__form',
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
            group = groups_service.create(
                name=appstruct['name'],
                authority=self.request.authority,
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
