# -*- coding: utf-8 -*-

from pyramid.view import view_config


# Deprecated dedicated endpoint for feature flag data,
# kept for compatibility with older clients (<= 0.8.6).
# Newer clients get feature flag data as part of the session data
# from the /app endpoint.
@view_config(route_name='features_status',
             request_method='GET',
             accept='application/json',
             renderer='json',
             http_cache=(0, {'no_store': False}))
def features_status(request):
    return request.feature.all()


def includeme(config):
    config.scan(__name__)
