import json

from horus import resources

from pyramid.interfaces import ILocation

from zope.interface import implementer

from h import api, models


@implementer(ILocation)
class BaseResource(resources.BaseFactory):
    """Base Resource class from which all resources are derived"""

    __name__ = None
    __parent__ = None


class InnerResource(BaseResource):
    """Helper Resource class for constructing traversal contexts

    Classes which inherit from this should contain attributes which are either
    class constructors for classes whose instances provide the
    :class:`pyramid.interfaces.ILocation` interface else attributes which are,
    themselves, instances of such a class. Such attributes are treated as
    valid traversal children of the Resource whose path component is the name
    of the attribute.
    """

    def __getitem__(self, name):
        """
        Any class attribute which is an instance providing
        :class:`pyramid.interfaces.ILocation` will be returned as is.

        Attributes which are constructors for implementing classes will
        be replaced with a constructed instance by reifying the newly
        constructed resource in place of the attribute.

        Assignment to the sub-resources `__name__` and `__parent__` properties
        is handled automatically.
        """

        factory_or_resource = getattr(self, name, None)

        if factory_or_resource:
            if ILocation.implementedBy(factory_or_resource):
                inst = factory_or_resource(self.request)
                inst.__name__ = name
                inst.__parent__ = self
                setattr(self, name, inst)
                return inst

            if ILocation.providedBy(factory_or_resource):
                return factory_or_resource

        raise KeyError(name)


class RootFactory(InnerResource, resources.RootFactory):
    pass


class AppFactory(BaseResource):
    def __init__(self, request):
        super(AppFactory, self).__init__(request)

    @property
    def embed(self):
        env = {
            pkg: json.dumps(self.request.webassets_env[pkg].urls())
            for pkg in ['inject', 'jquery', 'raf']
        }
        env['app'] = "'%s'" % self.request.resource_url(self)
        return env

    @property
    def persona(self):
        request = self.request

        # Transition code until multiple sign-in is implemented
        if request.user:
            return {
                'username': request.user.username,
                'provider': request.host,
            }

        return None

    @property
    def personas(self):
        request = self.request

        # Transition code until multiple sign-in is implemented
        if request.user:
            return [self.persona]

        return []

    @property
    def consumer(self):
        settings = self.request.registry.settings
        key = settings['api.key']
        consumer = models.Consumer.get_by_key(key)
        assert(consumer)
        return consumer

    @property
    def token(self):
        message = {
            'consumerKey': str(self.consumer.key),
            'ttl': self.consumer.ttl,
        }

        if self.persona:
            message['userId'] = 'acct:%(username)s@%(provider)s' % self.persona

        return api.auth.encode_token(message, self.consumer.secret)

    @property
    def token_url(self):
        return self.request.route_url('token')

    def __json__(self, request=None):
        return {
            name: getattr(self, name)
            for name in ['persona', 'personas', 'token', 'token_url']
        }


def includeme(config):
    config.set_root_factory(RootFactory)
    config.add_route('index', '/')
    RootFactory.app = AppFactory
