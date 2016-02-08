# -*- coding: utf-8 -*-


def includeme(config):
    config.add_route('api', '/', factory='h.api.resources.create_root')
    config.add_route('token', '/token')

    config.include('h.features')
    config.include('h.api.db')
    config.include('h.api.search')
    config.include('h.api.views')
