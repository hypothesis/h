# -*- coding: utf-8 -*-
from pyramid.events import BeforeRender, subscriber
from pyramid.renderers import get_renderer


@subscriber(BeforeRender)
def add_renderer_globals(event):
    request = event['request']

    # Set the base url to use in the <base> tag
    if hasattr(request, 'root'):
        event['base_url'] = request.resource_url(request.root, '')

    # Set the service url to use for API discovery
    event['service_url'] = request.resource_url(request.root, 'api', '')

    # Set the blocks property to refer to the block helpers template
    event['blocks'] = get_renderer('h:templates/blocks.pt').implementation()


def includeme(config):
    config.scan(__name__)
