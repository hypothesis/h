from beaker.session import Session, SessionObject
from beaker.util import coerce_session_params
from pyramid.interfaces import ISession
from pyramid.settings import asbool
from pyramid_beaker import BeakerSessionFactoryConfig
from zope.interface import implementer


def AngularSessionFactoryConfig(**options):
    class PyramidAngularSessionObject(SessionObject):
        _csrft_options = {
            'key': 'XSRF-TOKEN',
            'cookie_domain': options.get('cookie_domain'),
            'cookie_expires': options.get('cookie_expires', True),
            'cookie_path': options.get('cookie_path', '/'),
            'secure': options.get('secure', False),
        }

        def __init__(self, request):
            super(PyramidAngularSessionObject, self).__init__(request)
            self.__dict__['_csrft_cookie_'] = None

            def csrft_callback(request, response):
                exception = getattr(request, 'exception', None)
                if (exception is None or self._cookie_on_exception
                    and self.accessed()
                ):
                    self.persist()
                    csrft_cookie = self.__dict__['_csrft_cookie_']
                    if csrft_cookie and csrft_cookie.is_new:
                        value = csrft_cookie.request['cookie_out']
                        response.headerlist.append(('Set-Cookie', value))
            request.add_response_callback(csrft_callback)

        def new_csrf_token(self):
            # A beaker Session is used to avoid duplicating all the
            # messy cookie manipulation code, even though it's only used
            # to store the CSRF token. It has the same path, domain, and
            # security settings as the main session cookie.
            token = super(PyramidAngularSessionObject, self).new_csrf_token()
            csrft_cookie = Session({}, id=token, **self._csrft_options)
            csrft_cookie._set_cookie_values()
            csrft_cookie._update_cookie_out()
            self.__dict__['_csrft_cookie_'] = csrft_cookie
            return token

        def invalidate(self):
            # Easiest thing to do is eagerly create a new csrf immediately
            self._session().invalidate()
            self.new_csrf_token()

    # Construct a beaker session.
    BeakerSession = BeakerSessionFactoryConfig(**options)

    # Mix in handling of the CSRF Token Cookie.
    AngularSession = type(
        'PyramidAngularSessionObject',
        (PyramidAngularSessionObject, BeakerSession),
        {},
    )
    return implementer(ISession)(AngularSession)


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
