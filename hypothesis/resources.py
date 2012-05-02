from glob import glob
from os.path import basename, join, relpath, splitext
from operator import concat

from webassets import Bundle

def register_annotator(environment, *plugins):
    # Path utilities
    _name = lambda src: splitext(basename(src))[0]
    _src = lambda name: join('annotator', 'src', '%s.coffee' % name)
    _plugin = lambda name: join('annotator', 'src', 'plugin', '%s.coffee' % name)
    _lib = lambda src: Bundle(
        src, debug=False, filters='coffeescript',
        output=join('js', 'lib', 'annotator',
                    splitext(relpath(src, join('annotator', 'src')))[0]) + '.js')

    # Bundles
    lib = map(_lib, map(_src, ['extensions', 'console', 'class', 'range']))
    ui = map(_lib, map(_src, ['notification', 'widget', 'editor', 'viewer']))
    plugins = map(_lib, map(_plugin, plugins))
    js = Bundle(*(lib + [_lib(_src('annotator'))] +  ui + plugins))

    # Registration
    environment.register(
        'annotator_css',
        join('annotator', 'css', 'annotator.css'),
        filters='cssrewrite',
        output=join('css', 'annotator.min.css'))
    environment.register(
        'annotator_js',
        js,
        output=join('js', 'annotator.min.js'))

def register_bundles(environment):
    register_annotator(
        environment,
        'auth',
        'store',
        'unsupported')
    environment.register(
        'site_css',
        'sass/site.scss',
        debug=False,
        filters='compass',
        output='css/site.min.css')

def includeme(config):
    config.include('pyramid_webassets')
    assets_environment = config.get_webassets_env()
    register_bundles(assets_environment)

    config.include('pyramid_jinja2')
    config.add_jinja2_extension('webassets.ext.jinja2.AssetsExtension')
    config.get_jinja2_environment().assets_environment = assets_environment

    config.add_route('home', '/')
    config.add_route('token', '/api/token')
    config.add_route('api', '/api/*subpath')
