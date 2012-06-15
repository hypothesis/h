from glob import glob
from os.path import basename, dirname, join, relpath, splitext
from operator import concat

from pyramid.events import subscriber
from pyramid.events import BeforeRender
from pyramid.settings import aslist

from pyramid_webassets import add_webasset, IWebAssetsEnvironment

from webassets import Bundle
from webassets.loaders import YAMLLoader

def annotator_bundle(config):
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

    return Bundle(
        js,
        filters='uglifyjs',
        output='js/annotator.min.js'
    )

def add_webassets(config):
    add_webasset(config, 'annotator', annotator_bundle(config))
    loader = YAMLLoader(join(dirname(__file__), 'resources.yaml'))
    bundles = loader.load_bundles()
    for name in bundles:
        config.add_webasset(name, bundles[name])

@subscriber(BeforeRender)
def add_global(event):
    environment = event['request'].registry.queryUtility(IWebAssetsEnvironment)
    event['environment'] = environment

def includeme(config):
    config.add_route('home', '/', use_global_views=True)
    config.add_route('embed', '/embed.js')
    config.add_route('token', '/api/token')
    config.add_route('api', '/api/*subpath')

    config.scan(__name__)
    config.include('pyramid_webassets')
    add_webassets(config)
