# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.features.client import Client

__all__ = ('Client',)


def includeme(config):
    config.add_request_method(Client, name='feature', reify=True)

    config.add_subscriber('h.features.subscribers.remove_old_flags',
                          'pyramid.events.ApplicationCreated')
    config.add_subscriber('h.features.subscribers.preload_flags',
                          'pyramid.events.NewRequest')
