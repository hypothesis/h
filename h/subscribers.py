# -*- coding: utf-8 -*-


def add_renderer_globals(event):
    request = event['request']
    event['base_url'] = request.route_url('index')
    event['service_url'] = request.route_url('api')
    event['feature'] = request.feature

    # Add Google Analytics
    ga_tracking_id = request.registry.settings.get('ga_tracking_id')
    if ga_tracking_id is not None:
        event['ga_tracking_id'] = ga_tracking_id
        if 'localhost' in request.host:
            event['ga_create_options'] = "'none'"
        else:
            event['ga_create_options'] = "'auto'"


def set_user_from_oauth(event):
    """A subscriber that checks requests for OAuth credentials and sets the
    'REMOTE_USER' environment key to the authorized user (or ``None``)."""
    request = event.request
    request.verify_request()
    request.environ['REMOTE_USER'] = getattr(request, 'user', None)
