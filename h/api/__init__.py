# -*- coding: utf-8 -*-


def includeme(config):
    config.include('h.api.db')
    config.include('h.api.search')
    config.include('h.api.views')
