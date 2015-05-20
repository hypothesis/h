# -*- coding: utf-8 -*-


def add_renderer_globals(event):
    request = event['request']
    # Set the base url to use in the <base> tag
    event['base_url'] = request.resource_url(request.root, '')
    # Set the service url to use for API discovery
    event['service_url'] = request.resource_url(request.root, 'api', '')

    # Add Google Analytics
    ga_tracking_id = request.registry.settings.get('ga_tracking_id')
    if ga_tracking_id is not None:
        event['ga_tracking_id'] = ga_tracking_id
        if 'localhost' in request.host:
            event['ga_create_options'] = "'none'"
        else:
            event['ga_create_options'] = "'auto'"
