# -*- coding: utf-8 -*-


def includeme(config):
    config.include('h.views.exceptions')
    config.include('h.views.help')
    config.include('h.views.home')
    config.include('h.views.main')
    config.include('h.views.client')
    config.include('h.views.panels')
