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
    kw.setdefault('filters', 'cleancss,compass,cssrewrite')
    return Bundle(*names, **kw)


def Handlebars(*names, **kw):
    kw.setdefault('filters', 'handlebars')
    return Bundle(*names, **kw)


# Included dependencies
annotator = Bundle('h:lib/annotator.min.js', 'h:lib/annotator.*.min.js')
angular = Bundle('h:lib/angular.min.js', 'h:lib/angular-*.min.js')
d3 = Bundle('h:lib/d3.v2.min.js')
easyXDM = Bundle('h:lib/easyXDM.min.js')
jwz = Bundle('h:lib/jwz.min.js')
pagedown = Uglify('h:lib/Markdown.Converter.js')
raf = Uglify('h:lib/polyfills/raf.js')
underscore = Bundle('h:lib/underscore-min.js')


# External dependencies
jquery = Bundle('deform:static/scripts/jquery-1.7.2.min.js')
deform = Bundle(
    jquery,
    Uglify(
        'deform:static/scripts/jquery.form-3.09.js',
        'deform:static/scripts/deform.js',
        output='js/deform.min.js'
    )
)


# Handlebars templates
templates = Bundle(
    'h:lib/handlebars-runtime.min.js',
    Uglify(
        Handlebars('h:templates/*.handlebars', output='js/templates.js'),
        output='js/templates.min.js'
    ),
)


# Base and common SCSS
base = ['h:css/base.scss']
common = ['h:css/base.scss', 'h:css/common.scss']


# Main resource bundles
app = Bundle(
    jquery,
    angular,
    annotator,
    deform,
    d3,
    easyXDM,
    jwz,
    pagedown,
    templates,
    underscore,
    'h:lib/jquery.mousewheel.min.js',
    Uglify(
        *[
            Coffee('h:/js/%s.coffee' % name,
                   output='js/%s.js' % name)
            for name in
            (
                'app',
                'deform',
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
            Coffee('h:/js/plugin/%s.coffee' % name,
                   output='js/plugin/%s.js' % name)
            for name in
            (
                'heatmap',
            )
        ],
        output='js/hypothesis.plugins.min.js'
    ),
    SCSS('h:css/app.scss', depends=(base + common), output='css/app.css'),
)


site = SCSS('h:css/site.scss', depends=(base + common), output='css/site.css')


# The inject is a easyXDM consumer which loads the annotator in an iframe
# and sets up a JSON-RPC channel for cross-domain communication between the
# iframe and the host window.
inject = Bundle(
    easyXDM,
    'h:lib/annotator.min.js',
    Uglify(
        Coffee('h:js/inject/host.coffee', output='js/host.js'),
        output='js/hypothesis-host.min.js'
    ),
    SCSS('h:css/inject.scss', depends=base, output='css/inject.css'),
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

    config.add_static_view('css', 'h:css')
    config.add_static_view('js', 'h:js')
    config.add_static_view('lib', 'h:lib')
    config.add_static_view('images', 'h:images')

    loader = PythonLoader(config.registry.settings.get('h.assets', __name__))
    bundles = loader.load_bundles()
    for name in bundles:
        config.add_webasset(name, bundles[name])

    from deform.field import Field
    resource_registry = WebassetsResourceRegistry(config.get_webassets_env())
    Field.set_default_resource_registry(resource_registry)
    config.registry.resources = resource_registry
