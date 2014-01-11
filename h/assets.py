from os import path
from urlparse import urlparse

import re
import sys

if 'gevent' in sys.modules:
    import gevent.subprocess
    sys.modules['subprocess'] = gevent.subprocess

import pyramid

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

# Gettext
gettext = Uglify('lib/gettext.js', output='lib/gettext.min.js')

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
annotator_toolbar = Uglify(
    Coffee('js/plugin/toolbar.coffee', output='js/plugin/toolbar.js')
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
annotator_dtm = Uglify(
    Coffee('lib/dom_text_mapper.coffee', output='js/dom_text_mapper.js'),
    'lib/annotator.domtextmapper.js',
    output='lib/annotator.dtm.min.js'
)
annotator_texthl = Uglify(
    'lib/annotator.texthighlights.js',
    output='lib/annotator.texthighlights.min.js'
)
annotator_textanchors = Uglify(
    'lib/annotator.textanchors.js',
    output='lib/annotator.textanchors.min.js'
)
annotator_fuzzytext = Uglify(
    Uglify('lib/diff_match_patch_uncompressed.js', output='lib/diff_match_patch.js'),
    Coffee('lib/text_match_engines.coffee', output='js/text_match_engines.js'),
    Coffee('lib/dom_text_matcher.coffee', output='js/dom_text_matcher.js'),
    'lib/annotator.fuzzytextanchors.js',
    output='lib/annotator.fuzzytextanchors.min.js'
)
annotator_pdf = Uglify(
    Coffee('lib/page_text_mapper_core.coffee', output='js/page_text_mapper_core.js'),    
    'lib/annotator.pdf.js',
    output='lib/annotator.pdf.min.js'
)
annotator_threading = Uglify(
    Coffee('js/plugin/threading.coffee', output='js/plugin/threading.js')
)
annotator_i18n = Uglify(
    'locale/data.js',
    output='locale/data.min.js'
)

# Angular
angular = Uglify('lib/angular.js', output='lib/angular.min.js')
angular_animate = Uglify(
    'lib/angular-animate.js',
    output='lib/angular-animate.min.js'
)
angular_bootstrap = Uglify(
    'lib/angular-bootstrap.js',
    output='lib/angular-bootstrap.min.js'
)
angular_resource = Uglify(
    'lib/angular-resource.js',
    output='lib/angular-resource.min.js'
)

angular_route = Uglify(
    'lib/angular-route.js',
    output='lib/angular-route.min.js'
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
jquery_scrollintoview = Uglify(
    'lib/jquery.scrollintoview.js', output='lib/jquery.scrollintoview.min.js'
)

# jQuery UI
jquery_ui = Bundle(
    Uglify('h:lib/jquery.ui.widget.js', output='lib/jquery.ui.widget.min.js'),
    Uglify('h:lib/jquery.ui.autocomplete.js', output='lib/jquery.ui.autocomplete.min.js'),
    Uglify('h:lib/jquery.ui.core.js', output='lib/jquery.ui.core.min.js'),
    Uglify('h:lib/jquery.ui.widget.js', output='lib/jquery.ui.widget.min.js'),
    Uglify('h:lib/jquery.ui.menu.js', output='lib/jquery.ui.menu.min.js'),
    Uglify('h:lib/jquery.ui.position.js', output='lib/jquery.ui.position.min.js'),
    CSS('h:lib/jquery-ui-smoothness.css', output='lib/jquery-ui-smoothness.min.css'),
)

jquery_ui_effects = Bundle(
    Uglify('h:lib/jquery.ui.effect.js', output='lib/jquery.ui.effect.min.js'),
    Uglify('h:lib/jquery.ui.effect-blind.js', output='lib/jquery.ui.effect-blind.min.js'),
    Uglify('h:lib/jquery.ui.effect-highlight.js', output='lib/jquery.ui.effect-highlight.min.js'),
    Uglify('h:lib/jquery.ui.effect-forecolor-highlight.js', output='lib/jquery.ui.effect-forecolor-highlight.min.js')
)

# Polyfills
raf = Uglify('lib/polyfills/raf.js', output='lib/polyfills/raf.min.js')

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

visualsearch = Bundle(
    Uglify('h:lib/underscore-1.4.3.js', output='lib/underscore.min.js'),
    Uglify('h:lib/backbone-0.9.10.js', output='lib/backbone.min.js'),
    jquery_ui,
    Uglify('h:lib/visualsearch.js', output='lib/visualsearch.min.js'),
    CSS('h:lib/visualsearch.css', output='lib/visualsearch.min.css'),
)

momentjs = Bundle(
    Uglify('lib/moment-with-langs.js', output='lib/moment.min.js'),
    Uglify('lib/jstz.js', output='lib/jstz.min.js'),
    Uglify('lib/moment-timezone.js', output='lib/moment-timezone.min.js'),
    Uglify('lib/moment-timezone-data.js', output='lib/moment-timezone-data.min.js')
)

uuid = Uglify('lib/uuid.js', output='lib/uuid.min.js')

# SCSS
css_base = ['css/base.scss']
css_common = ['css/common.scss', 'css/responsive.scss', 'css/yui_grid.scss']


# Main resource bundles
app = Bundle(
    jquery,
    jquery_mousewheel,
    angular,
    angular_animate,
    angular_bootstrap,
    angular_resource,
    angular_route,
    angular_sanitize,
    gettext,
    annotator_i18n,
    annotator,
    annotator_auth,
    annotator_bridge,
    annotator_discovery,
    annotator_permissions,
    annotator_store,
    annotator_threading,
    annotator_document,
    jschannel,
    jwz,
    pagedown,
    raf,
    sockjs,
    jquery_ui,
    jquery_ui_effects,
    momentjs,
    tagit,
    visualsearch,
    uuid,
    Uglify(
        *[
            Coffee('js/%s.coffee' % name,
                   output='js/%s.js' % name)
            for name in
            (
                'app',
                'controllers',
                'filters',
                'flash',
                'directives',
                'app_directives',
                'displayer',
                'services',
                'streamfilter',
                'streamsearch',
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


# The inject bundle is intended to be loaded into pages for bootstrapping
# the application. It sets up RPC channels for cross-domain communication
# between frames participating in annotation by using the annotator bridge
# plugin.
inject = Bundle(
    d3,
    jquery,
    jquery_scrollintoview,
    jquery_ui,
    jquery_ui_effects,
    jschannel,
    gettext,
    annotator_i18n,
    annotator,
    annotator_bridge,
    annotator_document,
    annotator_heatmap,
    annotator_texthl,
    annotator_dtm,
    annotator_textanchors,
    annotator_fuzzytext,
    annotator_pdf,
    annotator_toolbar,
    Uglify(
        Coffee('js/guest.coffee', output='js/guest.js'),
        Coffee('js/host.coffee', output='js/host.js'),
        output='js/inject.min.js'
    ),
    SCSS('css/inject.scss', depends=css_base, output='css/inject.css'),
)

sidebar = SCSS('css/sidebar.scss', depends=(css_base + css_common),
               output='css/sidebar.min.css')

site = Bundle(
    app,
    SCSS('css/site.scss', depends=(css_base + css_common),
         output='css/site.min.css'),
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


class AssetRequest(object):
    def __init__(self, val, config):
        self.env = config.get_webassets_env()
        self.val = val

    def text(self):
        return 'asset_request = %s' % (self.val,)

    phash = text

    def __call__(self, event):
        request = event.request
        if request.matched_route is None:
            return False
        else:
            return request.matched_route.pattern.startswith(self.env.url)


def asset_response_subscriber(event):
    event.response.headers['Access-Control-Allow-Origin'] = '*'


def includeme(config):
    config.include('pyramid_webassets')

    env = config.get_webassets_env()

    # Configure the static views
    if env.url_expire is not False:
        # Cache for one year (so-called "far future" Expires)
        config.add_static_view(env.url, env.directory, cache_max_age=31536000)
    else:
        config.add_static_view(env.url, env.directory)

    # Set up a predicate and subscriber to set CORS headers on asset responses
    config.add_subscriber_predicate('asset_request', AssetRequest)
    config.add_subscriber(
        asset_response_subscriber,
        pyramid.events.NewResponse,
        asset_request=True
    )

    loader = PythonLoader(config.registry.settings.get('h.assets', __name__))
    bundles = loader.load_bundles()
    for bundle_name in bundles:
        log.info('name: ' + str(bundle_name))
        config.add_webasset(bundle_name, bundles[bundle_name])

    from deform.field import Field
    resource_registry = WebassetsResourceRegistry(config.get_webassets_env())
    Field.set_default_resource_registry(resource_registry)
    config.registry.resources = resource_registry
