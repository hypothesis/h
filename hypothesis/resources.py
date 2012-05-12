from glob import glob
from os.path import basename, relpath, splitext
from operator import concat

from pyramid.events import subscriber
from pyramid.events import BeforeRender
from pyramid.settings import aslist

from pyramid_webassets import add_webasset, IWebAssetsEnvironment

from webassets import Bundle

def register_annotator(config):
    # Path utilities
    _name = lambda src: splitext(basename(src))[0]
    _src = lambda name: 'annotator/src/%s.coffee' % name
    _plugin = lambda name: 'annotator/src/plugin/%s.coffee' % name
    _lib = lambda src: Bundle(
        src, debug=False, filters='coffeescript',
        output='js/lib/annotator/%s' %
                    splitext(relpath(src, 'annotator/src'))[0] + '.js')

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
        'annotator',
        Bundle(
            js,
            output='js/annotator.min.js'))

def add_webassets(config):
    environment = config.registry.queryUtility(IWebAssetsEnvironment)
    register_annotator(config)
    add_webasset(
        config,
        'jquery',
        Bundle(
            'annotator/lib/vendor/jquery.js',
            output='js/jquery.min.js'))
    add_webasset(config, 'd3', Bundle('js/lib/d3.v2.min.js', debug=False))
    add_webasset(
        config,
        'app_css',
        Bundle(
            Bundle('sass/app.scss',
                   debug=False,
                   filters='compass',
                   output='css/app.css'),
            output='css/hypothesis.min.css'))
    add_webasset(
        config,
        'app_js',
        Bundle(
            environment['d3'],
            environment['annotator'],
            Bundle('js/src/hypothesis.coffee',
                   debug=False,
                   filters='coffeescript',
                   output='js/lib/hypothesis.js'),
            output='js/hypothesis.min.js'))
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
