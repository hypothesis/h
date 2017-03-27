# -*- coding: utf-8 -*-

import platform

from pyramid.view import view_config

from h import __version__


@view_config(route_name='admin_index',
             request_method='GET',
             renderer='h:templates/admin/index.html.jinja2',
             permission='admin_index')
def index(_):
    return {
        'release_info': {
            'hostname': platform.node(),
            'python_version': platform.python_version(),
            'version': __version__,
        }
    }
