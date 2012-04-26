def includeme(config):
    # Set up the routes
    config.add_route('home', '/')
    config.add_route('token', '/api/token')
    config.add_route('api', '/api/*subpath')

    # Set up webassets
    config.include('pyramid_webassets')
    # See https://github.com/sontek/pyramid_webassets/issues/1
    config.get_webassets_env().manifest = False

    # Set up static views
    config.add_static_view('assets/css', 'resources/css')
    config.add_static_view('assets/images', 'resources/images')
