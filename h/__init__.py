def includeme(config):
    config.include('.api')
    config.include('.app')
    config.include('.models')
    config.include('.resources')
    config.include('.views')

def create_app(settings):
    from pyramid.config import Configurator
    config = Configurator(settings=settings)
    config.include(includeme)
    return config.make_wsgi_app()

def main(global_config, **settings):
    return create_app(settings)
