# -*- coding: utf-8 -*-

import deform
from pyramid import security
from pyramid.httpexceptions import (HTTPMovedPermanently, HTTPNoContent,
                                    HTTPSeeOther)
from pyramid.view import view_config, view_defaults

from h import i18n
from h import presenters
from h.groups import schemas

_ = i18n.TranslationString


@view_defaults(route_name='group_create',
               renderer='h:templates/groups/create.html.jinja2',
               effective_principals=security.Authenticated)
class GroupCreateController(object):
    def __init__(self, request):
        self.request = request
        self.schema = schemas.GroupSchema().bind(request=self.request)

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
        try:
            appstruct = self.form.validate(self.request.POST.items())
        except deform.ValidationFailure:
            return self._template_data()

        groups_service = self.request.find_service(name='groups')
        group = groups_service.create(name=appstruct['name'],
                                      userid=self.request.authenticated_userid)

        url = self.request.route_path('group_read',
                                      pubid=group.pubid,
                                      slug=group.slug)
        return HTTPSeeOther(url)

    def _template_data(self):
        """Return the data needed to render this controller's page."""
        return {'form': self.form.render()}


@view_config(route_name='group_read',
             request_method='GET',
             renderer='h:templates/groups/share.html.jinja2',
             effective_principals=security.Authenticated)
def read(group, request):
    """Group view for logged-in users."""
    _check_slug(group, request)

    # If the current user is not a member of the group, they will not have the
    # 'read' permission on the group. In this case, we show them the join
    # page.
    if not request.has_permission('read'):
        request.override_renderer = 'h:templates/groups/join.html.jinja2'
        return {'group': group}

    return {'group': group,
            'document_links': [presenters.DocumentHTMLPresenter(d).link
                               for d in group.documents()],
            'meta_attrs': [
                # Ask browsers not to send the page's URL (which can be used to
                # join the group) to other websites in the Referer header.
                {'name': 'referrer', 'content': 'origin'},
                          ],
            }


@view_config(route_name='group_read',
             request_method='GET',
             renderer='h:templates/groups/join.html.jinja2')
def read_unauthenticated(group, request):
    """Group view for logged-out users, allowing them to join the group."""
    _check_slug(group, request)
    return {'group': group}


@view_config(route_name='group_read_noslug', request_method='GET')
def read_noslug(group, request):
    _check_slug(group, request)


@view_config(route_name='group_read',
             request_method='POST',
             effective_principals=security.Authenticated)
def join(group, request):
    groups_service = request.find_service(name='groups')
    groups_service.member_join(group, request.authenticated_userid)

    url = request.route_path('group_read', pubid=group.pubid, slug=group.slug)
    return HTTPSeeOther(url)


@view_config(route_name='group_leave',
             request_method='POST',
             effective_principals=security.Authenticated)
def leave(group, request):
    groups_service = request.find_service(name='groups')
    groups_service.member_leave(group, request.authenticated_userid)

    return HTTPNoContent()


def _check_slug(group, request):
    """Redirect if the request slug does not match that of the group."""
    slug = request.matchdict.get('slug')
    if slug is None or slug != group.slug:
        raise HTTPMovedPermanently(request.route_path('group_read',
                                                      pubid=group.pubid,
                                                      slug=group.slug))


def includeme(config):
    config.scan(__name__)  # pragma: no cover
