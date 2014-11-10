# -*- coding: utf-8 -*-
from pyramid.events import BeforeRender, subscriber


@subscriber(BeforeRender)
def add_renderer_globals(event):
    request = event['request']

    # Set the base url to use in the <base> tag
    if hasattr(request, 'root'):
        event['base_url'] = request.resource_url(request.root, '')

    # Set the service url to use for API discovery
    event['service_url'] = request.resource_url(request.root, 'api', '')


def includeme(config):
    config.scan(__name__)
