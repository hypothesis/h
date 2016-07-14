# -*- coding: utf-8 -*-


def includeme(config):
    config.include('h.activity.views')

    config.add_route('activity.search', '/search')
