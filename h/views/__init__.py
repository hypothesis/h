# -*- coding: utf-8 -*-


def includeme(config):
    config.include('h.views.exceptions')
    config.include('h.views.help')
    config.include('h.views.home')
    config.include('h.views.main')
    config.include('h.views.client')

    # homepage
    config.add_route('index', '/')
    config.add_route('via_redirect', '/via')

    # client
    config.add_route('embed', '/embed.js')
    config.add_route('widget', '/app.html')

    # help
    config.add_route('help', '/docs/help')
    config.add_route('onboarding', '/welcome')

    # main
    config.add_route('robots', '/robots.txt')
    config.add_route('session', '/app')
    config.add_route('stream', '/stream')
