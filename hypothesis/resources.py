def includeme(config):
    # Set up templates and assets
    config.include('pyramid_jinja2')
    config.include('pyramid_webassets')
    assets_environment = config.get_webassets_env()
    config.add_jinja2_extension('webassets.ext.jinja2.AssetsExtension')
    config.get_jinja2_environment().assets_environment = assets_environment

    # Set up the routes
    config.add_route('home', '/')
    config.add_route('token', '/api/token')
    config.add_route('api', '/api/*subpath')
