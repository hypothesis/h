# -*- coding: utf-8 -*-

import deform
from pyramid import httpexceptions as exc
from pyramid.view import view_config
from pyramid import renderers

from h import i18n
from h import models
from h import presenters
from h.groups import schemas

import h.session


_ = i18n.TranslationString


@view_config(route_name='group_create',
             request_method='GET',
             renderer='h:templates/groups/create.html.jinja2')
def create_form(request):
    """Render the form for creating a new group."""
    if request.authenticated_userid is None:
        raise exc.HTTPNotFound()

    form = _group_form(request)

    return {'form': form.render()}


def _send_group_notification(request, event_type, pubid):
    """Publishes a group join/leave notification."""
    # messages to the 'user' topic include the full session state
    # so that the receiver can publish notifications to clients which are
    # up to date wrt. changes made by the caller of _send_group_notification()
    #
    # the alternative would be to commit the DB transaction
    # prior to dispatching the notification
    data = {
      'type': event_type,
      'session_model': h.session.model(request),
      'userid': request.authenticated_userid,
      'group': pubid,
    }
    request.realtime.publish_user(data)


@view_config(route_name='group_create',
             request_method='POST',
             renderer='h:templates/groups/create.html.jinja2')
def create(request):
    """Respond to a submission of the create group form."""
    if request.authenticated_userid is None:
        raise exc.HTTPNotFound()

    form = _group_form(request)
    try:
        appstruct = form.validate(request.POST.items())
    except deform.ValidationFailure:
        return {'form': form.render()}

    group = models.Group(
        name=appstruct["name"], creator=request.authenticated_user)
    request.db.add(group)

    # We need to flush the db session here so that group.id will be generated.
    request.db.flush()

    _send_group_notification(request, 'group-join', group.pubid)

    url = request.route_url('group_read', pubid=group.pubid, slug=group.slug)
    return exc.HTTPSeeOther(url)


def _login_to_join(request, group):
    """Return the rendered "Login to join this group" page.

    This is the page that's shown when a user who isn't logged in visits a
    group's URL.

    """
    template_data = {'group': group}
    return renderers.render_to_response(
        renderer_name='h:templates/groups/join.html.jinja2',
        value=template_data, request=request)


def _read_group(request, group):
    """Return the rendered "Share this group" page.

    This is the page that's shown when a user who is already a member of a
    group visits the group's URL.

    """
    return renderers.render_to_response(
        renderer_name='h:templates/groups/share.html.jinja2',
        request=request,
        value={
            'group': group,
            'group_url': request.route_url('group_read',
                                           pubid=group.pubid,
                                           slug=group.slug),
            'document_links': [presenters.DocumentHTMLPresenter(document).link
                               for document in group.documents()]
        })


def _join(request, group):
    """Return the rendered "Join this group" page.

    This is the page that's shown when a user who is not a member of a group
    visits the group's URL.

    """
    url = request.route_url('group_read', pubid=group.pubid, slug=group.slug)
    template_data = {'group': group, 'join_url': url, 'is_logged_in': True}
    return renderers.render_to_response(
        renderer_name='h:templates/groups/join.html.jinja2',
        value=template_data, request=request)


@view_config(route_name='group_read', request_method='GET')
@view_config(route_name='group_read_noslug', request_method='GET')
def read(request):
    """Render the page for a group."""
    pubid = request.matchdict["pubid"]
    slug = request.matchdict.get("slug")

    group = models.Group.get_by_pubid(pubid)
    if group is None:
        raise exc.HTTPNotFound()

    if slug is None or slug != group.slug:
        url = request.route_url('group_read',
                                pubid=group.pubid,
                                slug=group.slug)
        return exc.HTTPMovedPermanently(url)

    if not request.authenticated_userid:
        return _login_to_join(request, group)
    else:
        if group in request.authenticated_user.groups:
            return _read_group(request, group)
        else:
            return _join(request, group)


@view_config(route_name='group_read',
             request_method='POST',
             renderer='h:templates/groups/read.html.jinja2')
def join(request):
    if request.authenticated_userid is None:
        raise exc.HTTPNotFound()

    pubid = request.matchdict["pubid"]
    group = models.Group.get_by_pubid(pubid)

    if group is None:
        raise exc.HTTPNotFound()

    group.members.append(request.authenticated_user)
    _send_group_notification(request, 'group-join', group.pubid)

    url = request.route_url('group_read', pubid=group.pubid, slug=group.slug)
    return exc.HTTPSeeOther(url)


def _group_form(request):
    schema = schemas.GroupSchema().bind(request=request)
    submit = deform.Button(title=_('Create a new group'),
                           css_class='primary-action-btn '
                                     'group-form__submit-btn '
                                     'js-create-group-create-btn')
    form = deform.Form(schema,
                       css_class='group-form__form',
                       buttons=(submit,))
    return form


@view_config(route_name='group_leave',
             request_method='POST')
def leave(request):
    if request.authenticated_userid is None:
        raise exc.HTTPNotFound()

    pubid = request.matchdict["pubid"]
    group = models.Group.get_by_pubid(pubid)

    if group is None:
        raise exc.HTTPNotFound()

    if request.authenticated_user not in group.members:
        raise exc.HTTPNotFound()

    group.members.remove(request.authenticated_user)
    _send_group_notification(request, 'group-leave', group.pubid)

    return exc.HTTPNoContent()


def includeme(config):
    config.add_route('group_create', '/groups/new')
    config.add_route('group_leave', '/groups/{pubid}/leave')

    # Match "/groups/<pubid>/": we redirect to the version with the slug.
    config.add_route('group_read', '/groups/{pubid}/{slug:[^/]*}')
    config.add_route('group_read_noslug', '/groups/{pubid}')
    config.scan(__name__)
