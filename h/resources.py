from glob import glob
from os.path import basename, dirname, join, relpath, splitext
from operator import concat

from pyramid.settings import aslist

from webassets import Bundle
from webassets.filter import register_filter
from webassets.loaders import YAMLLoader

from cleancss import CleanCSS

def add_webassets(config):
    loader = YAMLLoader(join(dirname(__file__), 'resources.yaml'))
    bundles = loader.load_bundles()
    for name in bundles:
        config.add_webasset(name, bundles[name])

def includeme(config):
    config.add_route('home', '/', use_global_views=True)
    config.add_route('embed', '/embed.js')
    config.add_route('token', '/api/token')
    config.add_route('users', '/api/u')
    config.add_route('api', '/api/*subpath')
    config.add_route('app', '/app')

    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('register', '/register')
    config.add_route('forgot', '/forgot')

    config.include('pyramid_webassets')

    # wrap coffeescript output in a closure
    config.get_webassets_env().config['coffee_no_bare'] = True

    # register our backported cleancss filter until webassets 0.8 is released
    register_filter(CleanCSS)

    add_webassets(config)
