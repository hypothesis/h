from beaker.util import coerce_session_params
from pyramid.interfaces import ISession
from pyramid.settings import asbool
from pyramid_beaker import BeakerSessionFactoryConfig
from zope.interface import implementer


def AngularSessionFactoryConfig(**options):
    PyramidBeakerSessionObject = BeakerSessionFactoryConfig(**options)

    class PyramidAngularSessionObject(PyramidBeakerSessionObject):
        def __init__(self, request):
            PyramidBeakerSessionObject.__init__(self, request)

            def csrft_callback(request, response):
                exception = getattr(request, 'exception', None)
                if exception is None and self.accessed():
                    csrft = self.get('_csrft_', None)
                    cookie = self.cookie
                    if csrft and self.dirty():
                        # Temporarily swap the cookie key and value
                        # for XSRF-TOKEN and the csrf_token. This motly avoids
                        # the need to work directly with the cookie and the
                        # beaker configuration options.
                        old = (self.key, self.id)
                        try:
                            self.key = 'XSRF-TOKEN'
                            self._set_cookie_values()
                            cookie[self.key].coded_value = csrft
                            value = cookie[self.key].output(header='')
                            response.headerlist.append(('Set-Cookie', value))
                        finally:
                            self.key, self.id = old
            request.add_response_callback(csrft_callback)

        def invalidate(self):
            # Easiest thing to do is eagerly create a new csrf immediately
            self._session().invalidate()
            self.new_csrf_token()

    return implementer(ISession)(PyramidAngularSessionObject)


# Lifted from pyramid_beaker
def session_factory_from_settings(settings):
    """ Return a Pyramid session factory using Beaker session settings
    supplied from a Paste configuration file"""
    prefixes = ('session.', 'beaker.session.')
    options = {}

    # Pull out any config args meant for beaker session. if there are any
    for k, v in settings.items():
        for prefix in prefixes:
            if k.startswith(prefix):
                option_name = k[len(prefix):]
                if option_name == 'cookie_on_exception':
                    v = asbool(v)
                options[option_name] = v

    options = coerce_session_params(options)
    return AngularSessionFactoryConfig(**options)


def includeme(config):
    session_factory = session_factory_from_settings(config.registry.settings)
    config.set_session_factory(session_factory)
