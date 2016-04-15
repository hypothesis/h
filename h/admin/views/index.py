# -*- coding: utf-8 -*-

from pyramid.view import view_config


@view_config(route_name='admin_index',
             request_method='GET',
             renderer='h:templates/admin/index.html.jinja2',
             permission='admin_index')
def index(_):
    return {}


def includeme(config):
    config.scan(__name__)
