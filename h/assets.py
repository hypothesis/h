from os import path
from urlparse import urlparse

import re
import sys

if 'gevent' in sys.modules:
    import gevent.subprocess
    sys.modules['subprocess'] = gevent.subprocess


from webassets import Bundle
from webassets.filter import register_filter
from webassets.filter.cssrewrite import urlpath
from webassets.filter.cssrewrite.base import CSSUrlRewriter
from webassets.loaders import PythonLoader

import logging
log = logging.getLogger(__name__)


class CSSVersion(CSSUrlRewriter):
    """Source filter to resolve urls in CSS files using the asset resolver.

    The 'cssrewrite' filter supplied with webassets will rewrite relative
    URLs in the CSS so that they are relative to the output path of the
    file so that paths are correct after merging CSS files from different
    sources. This filter is designed to run after that in order to resolve
    these URLs using the configured resolver so that the assets include
    version information even when referenced from the CSS.
    """

    name = 'cssversion'
    max_debug_level = 'merge'

    def replace_url(self, url):
        parsed = urlparse(url)
        if parsed.scheme:
            return url
        else:
            dirname = path.dirname(self.output_path)
            filepath = path.join(dirname, parsed.path)
            filepath = path.normpath(path.abspath(filepath))
            resolved = self.env.resolver.resolve_source_to_url(filepath, url)
            relative = urlpath.relpath(self.output_url, resolved)
            return relative

register_filter(CSSVersion)


def Uglify(*names, **kw):
    kw.setdefault('filters', 'uglifyjs')
    return Bundle(*names, **kw)


def Coffee(*names, **kw):
    kw.setdefault('filters', 'coffeescript')
    return Bundle(*names, **kw)


def SCSS(*names, **kw):
    kw.setdefault('filters', 'compass,cssrewrite,cssversion,cleancss')
    return Bundle(*names, **kw)


def CSS(*names, **kw):
    kw.setdefault('filters', 'cssrewrite,cssversion,cleancss')
    return Bundle(*names, **kw)

#
# Included dependencies
#

# Annotator
annotator = Uglify('lib/annotator.js', output='lib/annotator.min.js')
annotator_auth = Uglify(
    'lib/annotator.auth.js',
    output='lib/annotator.auth.min.js'
)
annotator_bridge = Uglify(
    Coffee('js/plugin/bridge.coffee', output='js/plugin/bridge.js')
)
annotator_discovery = Uglify(
    Coffee('js/plugin/discovery.coffee', output='js/plugin/discovery.js')
)
annotator_heatmap = Uglify(
    Coffee('js/plugin/heatmap.coffee', output='js/plugin/heatmap.js')
)
annotator_permissions = Uglify(
    'lib/annotator.permissions.js',
    output='lib/annotator.permissions.min.js'
)
annotator_store = Uglify(
    'lib/annotator.store.js',
    output='lib/annotator.store.min.js'
)
annotator_document = Uglify(
    'lib/annotator.document.js',
    output='lib/annotator.document.min.js'
)
annotator_threading = Uglify(
    Coffee('js/plugin/threading.coffee', output='js/plugin/threading.js')
)

# Angular
angular = Uglify('lib/angular.js', output='lib/angular.min.js')
angular_bootstrap = Uglify(
    'lib/angular-bootstrap.js',
    output='lib/angular-bootstrap.min.js'
)
angular_resource = Uglify(
    'lib/angular-resource.js',
    output='lib/angular-resource.min.js'
)
angular_sanitize = Uglify(
    'lib/angular-sanitize.js',
    output='lib/angular-sanitize.min.js'
)

# jQuery
jquery = Uglify('lib/jquery-1.10.2.js', output='lib/jquery-1.10.2.min.js')
jquery_mousewheel = Uglify(
    'lib/jquery.mousewheel.js', output='lib/jquery.mousewheel.min.js'
)

# jQuery UI
jquery_ui = Bundle(
    Uglify('h:lib/jquery.ui.core.js', output='lib/jquery.ui.core.min.js'),
    Uglify('h:lib/jquery.ui.widget.js', output='lib/jquery.ui.widget.min.js'),
    Uglify('h:lib/jquery.ui.position.js', output='lib/jquery.ui.position.min.js'),
    Uglify('h:lib/jquery.ui.menu.js', output='lib/jquery.ui.menu.min.js'),
    Uglify('h:lib/jquery.ui.autocomplete.js', output='lib/jquery.ui.autocomplete.min.js'),
    CSS('h:lib/jquery-ui-smoothness.css', output='lib/jquery-ui-smoothness.min.css'),
)

jquery_ui_effects = Bundle(
    Uglify('h:lib/jquery.ui.effect.js', output='lib/jquery.ui.effect.min.js'),
    Uglify('h:lib/jquery.ui.effect-blind.js', output='lib/jquery.ui.effect-blind.min.js'),
    Uglify('h:lib/jquery.ui.effect-highlight.js', output='lib/jquery.ui.effect-highlight.min.js')
)

# Polyfills
raf = Uglify('lib/polyfills/raf.js', output='lib/polyfills/raf.js.min')

# Others
d3 = Uglify('lib/d3.js', output='lib/d3.min.js')
deform = Bundle(
    jquery,
    Uglify('deform:static/scripts/deform.js', output='lib/deform.min.js'),
)
jschannel = Uglify('lib/jschannel.js', output='lib/jschannel.min.js')
jwz = Uglify('lib/jwz.js', output='lib/jwz.min.js')
pagedown = Uglify(
    'lib/Markdown.Converter.js',
    output='lib/Markdown.Converter.min.js'
)
sockjs = Uglify('h:lib/sockjs-0.3.4.js', output='lib/sockjs-client.min.js')
tagit = Uglify('h:lib/tag-it.js', output='lib/tag-it.min.js')

domTextFamily = Uglify(
    Coffee('lib/dom_text_mapper.coffee', output='js/dom_text_mapper.js'),
    Coffee('lib/dom_text_matcher.coffee', output='js/dom_text_matcher.js'),
    Coffee('lib/text_match_engines.coffee', output='js/text_match_engines.js'),
    Uglify('lib/diff_match_patch_uncompressed.js', output='lib/diff_match_patch.js'),
    output='lib/dom_text.min.js'
)

# SCSS
css_base = ['css/base.scss']
css_common = ['css/common.scss', 'css/responsive.scss', 'css/yui_grid.scss']


# Main resource bundles
app = Bundle(
    jquery,
    jquery_mousewheel,
    angular,
    angular_bootstrap,
    angular_resource,
    angular_sanitize,
    annotator,
    annotator_auth,
    annotator_bridge,
    annotator_discovery,
    annotator_heatmap,
    annotator_permissions,
    annotator_store,
    annotator_threading,
    annotator_document,
    d3,
    jschannel,
    jwz,
    pagedown,
    raf,
    sockjs,
    jquery_ui,
    jquery_ui_effects,
    tagit,
    Uglify(
        *[
            Coffee('js/%s.coffee' % name,
                   output='js/%s.js' % name)
            for name in
            (
                'app',
                'controllers',
                'filters',
                'directives',
                'app_directives',
                'displayer',
                'services',
                'streamer',
                'streamfilter',
                'stream',
            )
        ],
        output='js/app.min.js'
    ),
)

sidebar = SCSS('css/sidebar.scss', depends=(css_base + css_common),
               output='css/sidebar.min.css')

site = Bundle(
    app,
    SCSS('css/site.scss', depends=(css_base + css_common),
         output='css/site.min.css'),
)


# The inject is a script which loads the annotator in an iframe
# and sets up an RPC channel for cross-domain communication between the
# the frame and its parent window. It then makes cretain annotator methods
# available via the bridge plugin.
inject = Bundle(
    domTextFamily,
    jquery,
    jschannel,
    annotator,
    annotator_bridge,
    annotator_document,
    Uglify(
        Coffee('js/host.coffee', output='js/host.js'),
        output='js/host.min.js'
    ),
    SCSS('css/inject.scss', depends=css_base, output='css/inject.css'),
)


class WebassetsResourceRegistry(object):
    def __init__(self, env):
        self.env = env

    def __call__(self, requirements):
        result = {'js': [], 'css': []}

        urls = []
        for name in zip(*requirements)[0]:
            log.info('name: ' + str(name))
            if name in self.env:
                bundle = self.env[name]
                urls.extend(bundle.urls())

        for source in urls:
            # check asset type (js or css), modulo cache-busting qs
            for thing in ('js', 'css'):
                if re.search(r'\.%s(\??[^/]+)?$' % thing, source):
                    if not source in result[thing]:
                        result[thing].append(source)

        return result


def includeme(config):
    config.include('pyramid_webassets')

    env = config.get_webassets_env()
    kw = {}
    if env.url_expire is not False:
        # Cache for one year (so-called "far future" Expires)
        kw['cache_max_age'] = 31536000
    config.add_static_view(env.url, env.directory, **kw)

    loader = PythonLoader(config.registry.settings.get('h.assets', __name__))
    bundles = loader.load_bundles()
    for name in bundles:
        log.info('name: ' + str(name))
        config.add_webasset(name, bundles[name])

    from deform.field import Field
    resource_registry = WebassetsResourceRegistry(config.get_webassets_env())
    Field.set_default_resource_registry(resource_registry)
    config.registry.resources = resource_registry
