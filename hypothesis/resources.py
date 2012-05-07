from glob import glob
from os.path import basename, join, relpath, splitext
from operator import concat

from pyramid.events import subscriber
from pyramid.events import BeforeRender
from pyramid.settings import aslist

from pyramid_webassets import add_webasset, IWebAssetsEnvironment

from webassets import Bundle

def register_annotator(config):
    # Path utilities
    _name = lambda src: splitext(basename(src))[0]
    _src = lambda name: join('annotator', 'src', '%s.coffee' % name)
    _plugin = lambda name: join('annotator', 'src', 'plugin', '%s.coffee' % name)
    _lib = lambda src: Bundle(
        src, debug=False, filters='coffeescript',
        output=join('js', 'lib', 'annotator',
                    splitext(relpath(src, join('annotator', 'src')))[0]) + '.js')

    # Plugins
    plugins = aslist(config.get_settings().get('annotator.plugins', ''))
    plugins = map(_lib, map(_plugin, plugins))

    # Bundles
    lib = map(_lib, map(_src, ['extensions', 'console', 'class', 'range']))
    ui = map(_lib, map(_src, ['notification', 'widget', 'editor', 'viewer']))
    js = Bundle(*(lib + [_lib(_src('annotator'))] +  ui + plugins))

    # Registration
    add_webasset(
        config,
        'annotator_css',
        Bundle(
            join('annotator', 'css', 'annotator.css'),
            filters='cssrewrite',
            output=join('css', 'annotator.min.css')))
    add_webasset(
        config,
        'annotator_js',
        Bundle(
            js,
            output=join('js', 'annotator.min.js')))

def add_webassets(config):
    environment = config.registry.queryUtility(IWebAssetsEnvironment)
    register_annotator(config)
    add_webasset(
        config,
        'jquery',
        Bundle(
            'annotator/lib/vendor/jquery.js',
            output='js/jquery.min.js'))
    add_webasset(
        config,
        'hypothesis_css',
        Bundle(
            environment['annotator_css'],
            Bundle('sass/common.scss',
                   debug=False,
                   filters='compass',
                   output='css/common.css'),
            output='css/hypothesis.min.css'))
    add_webasset(
        config,
        'hypothesis_js',
        Bundle(
            environment['annotator_js'],
            Bundle('js/hypothesis.js'),
            output='js/hypothesis.min.js'))
    add_webasset(
        config,
        'hypothesis_full_js',
        Bundle(
            environment['hypothesis_js'],
            output='js/hypothesis-full.min.js'))
    add_webasset(
        config,
        'site_css',
        Bundle(
            'sass/site.scss',
            debug=False,
            filters='compass',
            output='css/site.css'))
    add_webasset(
        config,
        'css',
        Bundle(
               environment['annotator_css'],
               environment['site_css'],
               output='css/site-full.min.css'))

@subscriber(BeforeRender)
def add_global(event):
    event['environment'] = event['request'].registry.queryUtility(
        IWebAssetsEnvironment)

def includeme(config):
    config.add_route('home', '/', use_global_views=True)
    config.add_route('token', '/api/token')
    config.add_route('api', '/api/*subpath')

    config.scan(__name__)
    config.include('pyramid_webassets')
    add_webassets(config)
