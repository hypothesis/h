# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from jinja2 import Markup
from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPFound

from h import form  # noqa F401
from h import i18n
from h import models
from h import paginator
from h.schemas.admin_group import CreateAdminGroupSchema, user_exists_validator_factory

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
        user_validator = user_exists_validator_factory(request.find_service(name='user'))
        self.schema = CreateAdminGroupSchema(validator=user_validator).bind(request=request)
        self.request = request
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
            svc = self.request.find_service(name='group')

            # Create the new group.
            creator = appstruct['creator']
            authority = appstruct['authority']
            description = appstruct['description']
            name = appstruct['name']
            origins = appstruct['origins']
            type_ = appstruct['group_type']

            userid = models.User(username=creator, authority=authority).userid

            if type_ == 'open':
                group = svc.create_open_group(name=name, userid=userid,
                                              origins=origins, description=description)
            elif type_ == 'restricted':
                group = svc.create_restricted_group(name=name, userid=userid,
                                                    origins=origins, description=description)
            else:
                raise Exception('Unsupported group type {}'.format(type_))

            # Flush changes to allocate group a pubid
            self.request.db.flush(objects=[group])

            group_url = self.request.route_url('group_read', pubid=group.pubid, slug=group.slug)
            self.request.session.flash(Markup('Created new group <a href="{url}">{name}</a>'.format(
                                        name=name, url=group_url)), queue='success')

            # Direct the user back to the admin page.
            return HTTPFound(location=self.request.route_url('admin_groups'))

        return form.handle_form_submission(self.request, self.form,
                                           on_success=on_success,
                                           on_failure=self._template_context)

    def _template_context(self):
        return {'form': self.form.render()}
