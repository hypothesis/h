from pyramid.settings import asbool


class Client(object):
    """
    Client provides access to the current configuration of feature flags as
    recorded in the underlying storage.

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


class SettingsStorage(object):
    """
    SettingsStorage abstracts the loading of feature flags from a Pyramid
    settings object.

    Feature flags are settings with a boolean (or boolean-coerceable) value
    prefixed by the name of this feature module or a specified prefix. They
    might look like the following in a .ini file:

        h.features.widgets_enabled = True
    """
    def __init__(self, settings, prefix=__name__):
        self.settings = settings
        self.prefix = prefix

    def get(self, name):
        try:
            setting = self.settings[self.prefix + '.' + name]
        except KeyError:
            return None
        else:
            return asbool(setting)


class UnknownFeatureError(Exception):
    pass


def get_client(request):
    storage = SettingsStorage(request.registry.settings)
    return Client(storage)


def includeme(config):
    config.set_request_property(get_client, name='feature', reify=True)
