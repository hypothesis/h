import re

from webassets import Bundle
from webassets.loaders import PythonLoader


def Uglify(*names, **kw):
    kw.setdefault('filters', 'uglifyjs')
    return Bundle(*names, **kw)


def Coffee(*names, **kw):
    kw.setdefault('filters', 'coffeescript')
    return Bundle(*names, **kw)


def SCSS(*names, **kw):
    kw.setdefault('filters', 'compass,cssrewrite,cleancss')
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
annotator_permissions = Uglify(
    'lib/annotator.permissions.js',
    output='lib/annotator.permissions.min.js'
)
annotator_store = Uglify(
    'lib/annotator.store.js',
    output='lib/annotator.store.min.js'
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
angular_sanitize = Uglify(
    'lib/angular-sanitize.js',
    output='lib/angular-sanitize.min.js'
)

# jQuery
jquery = Uglify('lib/jquery-1.8.3.js', output='lib/jquery-1.8.3.min.js')
jquery_mousewheel = Uglify(
    'lib/jquery.mousewheel.js', output='lib/jquery.mousewheel.min.js'
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

domTextFamily = Bundle(
    Coffee('lib/dom_text_mapper.coffee', output='js/dom_text_mapper.js'),
    Coffee('lib/dom_text_matcher.coffee', output='js/dom_text_matcher.js'),
    Coffee('lib/text_match_engines.coffee', output='js/text_match_engines.js'),
    Uglify('lib/diff_match_patch_uncompressed.js', output='lib/diff_match_patch.js')
)

# Base and common SCSS
base = ['css/base.scss']
common = ['css/base.scss', 'css/common.scss']


# Main resource bundles
app = Bundle(
    jquery,
    jquery_mousewheel,
    angular,
    angular_bootstrap,
    angular_sanitize,
    annotator,
    annotator_auth,
    annotator_bridge,
    annotator_permissions,
    annotator_store,
    annotator_threading,
    d3,
    jschannel,
    jwz,
    pagedown,
    raf,
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
                'services',
            )
        ],
        output='js/hypothesis.min.js'
    ),
    Uglify(
        *[
            Coffee('js/plugin/%s.coffee' % name,
                   output='js/plugin/%s.js' % name)
            for name in
            (
                'heatmap',
            )
        ],
        output='js/hypothesis.plugins.min.js'
    ),
    SCSS('css/app.scss', depends=(base + common), output='css/app.css'),
)


site = SCSS('css/site.scss', depends=(base + common), output='css/site.css')


# The inject is a script which loads the annotator in an iframe
# and sets up an RPC channel for cross-domain communication between the
# the frame and its parent window. It then makes cretain annotator methods
# available via the bridge plugin.
inject = Bundle(
    jquery,
    jschannel,
    annotator,
    annotator_bridge,
    domTextFamily,
    Uglify(
        Coffee('js/inject/host.coffee', output='js/host.js'),
        output='js/hypothesis-host.min.js'
    ),
    SCSS('css/inject.scss', depends=base, output='css/inject.css'),
)


class WebassetsResourceRegistry(object):
    def __init__(self, env):
        self.env = env

    def __call__(self, requirements):
        result = {'js': [], 'css': []}

        urls = []
        for name in zip(*requirements)[0]:
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
        config.add_webasset(name, bundles[name])

    from deform.field import Field
    resource_registry = WebassetsResourceRegistry(config.get_webassets_env())
    Field.set_default_resource_registry(resource_registry)
    config.registry.resources = resource_registry
