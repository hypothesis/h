# -*- coding: utf-8 -*-

from pyramid.view import view_config

from h import models


@view_config(route_name='admin_badge',
             request_method='GET',
             renderer='h:templates/admin/badge.html.jinja2',
             permission='admin_badge')
def badge_index(_):
    return {"uris": models.Blocklist.all()}


@view_config(route_name='admin_badge',
             request_method='POST',
             request_param='add',
             renderer='h:templates/admin/badge.html.jinja2',
             permission='admin_badge')
def badge_add(request):
    try:
        request.db.add(models.Blocklist(uri=request.params['add']))
    except ValueError as err:
        request.session.flash(err.message, 'error')
    return badge_index(request)


@view_config(route_name='admin_badge',
             request_method='POST',
             request_param='remove',
             renderer='h:templates/admin/badge.html.jinja2',
             permission='admin_badge')
def badge_remove(request):
    uri = request.params['remove']
    request.db.delete(models.Blocklist.get_by_uri(uri))
    return badge_index(request)


def includeme(config):
    config.scan(__name__)
