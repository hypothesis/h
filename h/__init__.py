from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


def includeme(config):
    # Include horus framework and prerequisites
    config.include('h.forms')
    config.include('h.schemas')
    config.include('horus')
    config.commit()

    # Include authentication, API and models
    config.include('pyramid_multiauth')
    config.include('h.api')
    config.include('h.models')
    config.commit()

    # Include the rest of the application
    config.include('h.assets')
    config.include('h.layouts')
    config.include('h.panels')
    config.include('h.resources')
    config.include('h.session')
    config.include('h.subscribers')
    config.include('h.views')
    config.include('h.streamer')


def bootstrap(cfname, request=None, options=None, config_fn=None):
    """Bootstrap the application with the given paste configuration file

    An optional function argument may be supplied. This function will be
    invoked with the bootstrapping environment.
    """
    from pyramid import paster

    paster.setup_logging(cfname)
    env = paster.bootstrap(cfname, request=request, options=options)

    try:
        if config_fn:
            config_fn(env)
    finally:
        env['closer']()

    return env['app']


def create_app(settings):
    from pyramid.config import Configurator
    from pyramid.path import AssetResolver
    from pyramid.response import FileResponse

    config = Configurator(settings=settings)

    favicon = AssetResolver().resolve('h:favicon.ico')
    config.add_route('favicon', '/favicon.ico')
    config.add_view(
        lambda request: FileResponse(favicon.abspath(), request=request),
        route_name='favicon'
    )
    config.add_route('help', '/docs/help')

    config.add_route('ok', '/ruok')
    config.add_view(lambda request: 'imok', renderer='string', route_name='ok')

    # Include all the pyramid subcomponents
    config.include(includeme)

    return config.make_wsgi_app()


def main(global_config, **settings):
    settings.update(global_config)
    return create_app(settings)


def server(app, gcfg=None, host="127.0.0.1", port=None, *args, **kwargs):
    # Workaround for gunicorn #540
    # Remove after updating gunicorn > 17.5
    from gunicorn.config import get_default_config_file
    from gunicorn.app.pasterapp import PasterServerApplication

    cfgfname = kwargs.pop('config', get_default_config_file())

    paste_server = PasterServerApplication(
        app,
        gcfg=gcfg,
        host=host,
        port=port,
        *args,
        **kwargs
    )

    if cfgfname:
        paste_server.load_config_from_file(cfgfname)

    paste_server.run()
