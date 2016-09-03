# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.features.client import Client

__all__ = ('Client',)


def includeme(config):
    config.include('h.features.views')

    config.add_request_method(Client, name='feature', reify=True)

    config.add_subscriber('h.features.subscribers.remove_old_flags',
                          'pyramid.events.ApplicationCreated')
    config.add_subscriber('h.features.subscribers.preload_flags',
                          'pyramid.events.NewRequest')

    config.add_route('features_status', '/app/features')
