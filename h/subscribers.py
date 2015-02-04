# -*- coding: utf-8 -*-
def add_renderer_globals(event):
    request = event['request']
    # Set the base url to use in the <base> tag
    event['base_url'] = request.resource_url(request.root, '')
    # Set the service url to use for API discovery
    event['service_url'] = request.resource_url(request.root, 'api', '')
    # Allow templates to check for feature flags
    event['feature'] = request.registry.feature


def set_user_from_oauth(event):
    """A subscriber that checks requests for OAuth credentials and sets the
    'REMOTE_USER' environment key to the authorized user (or ``None``)."""
    request = event.request
    request.verify_request()
    request.environ['REMOTE_USER'] = getattr(request, 'user', None)
