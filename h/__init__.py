from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


def includeme(config):
    config.include('h.api')
    config.include('h.app')
    config.include('h.assets')
    config.include('h.forms')
    config.include('h.layouts')
    config.include('h.models')
    config.include('h.panels')
    config.include('h.resources')
    config.include('h.session')
    config.include('h.schemas')
    config.include('h.subscribers')
    config.include('h.views')


def bootstrap(cfname, config_fn=None):
    """Bootstrap the application with the given paste configuration file

    An optional function argument may be supplied. This function will be
    invoked with the bootstrapping environment.
    """
    from pyramid import paster

    paster.setup_logging(cfname)
    env = paster.bootstrap(cfname)

    try:
        if config_fn:
            config_fn(env)
    finally:
        env['closer']()

    return env['app']


def create_app(settings):
    from horus import groupfinder
    from pyramid.config import Configurator
    from pyramid.authentication import SessionAuthenticationPolicy
    from pyramid.authorization import ACLAuthorizationPolicy
    from pyramid.path import AssetResolver
    from pyramid.response import FileResponse

    authn_policy = SessionAuthenticationPolicy(callback=groupfinder)
    authz_policy = ACLAuthorizationPolicy()

    config = Configurator(
        settings=settings,
        authentication_policy=authn_policy,
        authorization_policy=authz_policy,
    )

    favicon = AssetResolver().resolve('h:favicon.ico')
    config.add_route('favicon', '/favicon.ico')
    config.add_view(
        lambda request: FileResponse(favicon.abspath(), request=request),
        route_name='favicon'
    )

    # Include the base configuration for horus integration
    config.include('h.forms')
    config.include('h.models')
    config.include('h.schemas')
    config.commit()

    # Include horus
    config.include('horus')
    config.commit()

    # Include the rest of the application
    config.include(includeme)

    return config.make_wsgi_app()


def main(global_config, **settings):
    settings.update(global_config)
    return create_app(settings)
