# -*- coding: utf-8 -*-


def add_renderer_globals(event):
    request = event['request']
    # Set the base url to use in the <base> tag
    event['base_url'] = request.resource_url(request.root, '')
    # Set the service url to use for API discovery
    event['service_url'] = request.resource_url(request.root, 'api', '')
    # Allow templates to check for feature flags
    event['feature'] = request.registry.feature
