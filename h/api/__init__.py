# -*- coding: utf-8 -*-
__all__ = ('create_root', 'includeme')
from h.api.resources import create_root


def includeme(config):
    config.add_route('api', '/', factory=create_root)
    config.add_route('access_token', '/access_token')

    # XXX: Client should be using /access_token, isn't yet.
    config.add_route('token', '/token')

    config.include('h.features')
    config.include('h.api.db')
    config.include('h.api.views')
