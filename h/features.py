# -*- coding: utf-8 -*-
from pyramid.settings import asbool


class Client(object):
    """
    Client provides access to the current configuration of feature flags as
    recorded in the underlying (dict-like) storage.

    Typical simple usage involves creating a client with a storage and then
    querying it for the current state of named features:

        feature = Client(storage)
        ...
        if feature('widgets_enabled'):
            widgets.enable()
    """

    def __init__(self, storage):
        self.storage = storage

    def __call__(self, name):
        res = self.storage.get(name)

        if res is None:
            raise UnknownFeatureError(name)

        return res


class UnknownFeatureError(Exception):
    pass


def get_client(config):
    """
    get_client returns a feature client configured using data found in the
    settings of the current application.
    """
    storage = _features_from_settings(config.registry.settings)

    return Client(storage)


def _features_from_settings(settings, prefix=__package__ + '.feature.'):
    storage = {}

    for k, v in settings.items():
        if k.startswith(prefix):
            storage[k[len(prefix):]] = asbool(v)

    return storage


def includeme(config):
    config.registry.feature = get_client(config)
