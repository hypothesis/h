import horus

from webassets import Bundle
from webassets.filter import register_filter
from webassets.loaders import PythonLoader

from h import api, app

# register our backported cleancss filter until webassets 0.8 is released
from h.cleancss import CleanCSS
register_filter(CleanCSS)

# The main annotation application is a combination of upstream Annotator
# core components and plugins with additional downstream plugins from here.
annotator = Bundle(
    Bundle(
        'h:js/lib/annotator.min.js',
        'h:js/lib/annotator.auth.min.js',
        'h:js/lib/annotator.permissions.min.js',
        'h:js/lib/annotator.store.min.js',
    ),
    Bundle('h:js/lib/jquery.mousewheel.min.js'),
    Bundle(
        Bundle(
            'h:js/src/plugin/heatmap.coffee',
            debug=False,
            filters='coffeescript',
            output='js/heatmap.js',
        ),
        Bundle(
            'h:js/src/hypothesis.coffee',
            debug=False,
            filters='coffeescript',
            output='js/hypothesis.js',
        ),
        filters='uglifyjs',
        output='js/hypothes.is.min.js',
    ),
)

# The injector is a easyXDM consumer which loads the annotator in an iframe
# and sets up a JSON-RPC channel for cross-domain communication between the
# iframe and the host window.
injector = Bundle(
    Bundle('h:js/lib/annotator.min.js'),
    Bundle(
        Bundle(
            'h:js/src/annotator.host.coffee',
            debug=False,
            filters='coffeescript',
            output='js/annotator.host.js',
        ),
        filters='uglifyjs',
        output='js/hypothesis-host.min.js',
    ),
)

# The full application dependencies are as follows, with easyXDM as a common
# component for both the annotator and injector.
d3 = Bundle('h:js/lib/d3.v2.min.js')
deform = Bundle(
    'deform:static/scripts/jquery.form-3.09.js',
    'deform:static/scripts/deform.js'
)
easyXDM = Bundle('h:js/lib/easyXDM.min.js')
handlebars = Bundle('h:js/lib/handlebars-runtime.min.js')
jquery = Bundle('deform:static/scripts/jquery-1.7.2.min.js')
jwz = Bundle('h:js/lib/jwz.min.js')
underscore = Bundle('h:js/lib/underscore-min.js')

# The user interface of the application is structured around these Handlebars
# templates.
_template = lambda tf: Bundle(
    'h:templates/%s.handlebars' % tf,
    filters=('handlebars',),
    debug=False,
    output='js/templates/%s.js' % tf)
templates = Bundle(
    _template('detail'),
    _template('editor'),
    _template('summary'),
    Bundle('h:js/lib/helpers.js'),
    filters=('uglifyjs',),
    output='js/hypothesis-templates.min.js',
)

# CSS specific to the application
app_css = Bundle(
    Bundle(
        'h:sass/app.scss',
        debug=False,
        depends=(
            'h:sass/reset.scss',
            'h:sass/base.scss',
            'h:sass/common.scss',
        ),
        filters=('compass', 'cssrewrite',),
        output='css/app.css',
    ),
    filters=('cleancss',),
    output='css/app.min.css',
)

# Host-page CSS for widget placement.
inject_css = Bundle(
    Bundle(
        'h:sass/inject.scss',
        debug=False,
        depends=('h:sass/base.scss',),
        filters=('compass', 'cssrewrite',),
        output='css/inject.css',
    ),
    filters=('cleancss', 'datauri'),
    output=('css/inject.min.css'),
)

# CSS specific to the destination site
site_css = Bundle(
    Bundle(
        'h:sass/site.scss',
        debug=False,
        depends=(
            'h:sass/reset.scss',
            'h:sass/base.scss',
            'h:sass/common.scss',
        ),
           filters=('compass', 'cssrewrite',),
        output='css/site.css',
    ),
    filters=('cleancss',),
    output='css/site.min.css',
)


def add_webassets(config):
    config.include('pyramid_webassets')
    loader = PythonLoader(__name__)
    bundles = loader.load_bundles()
    for name in bundles:
        config.add_webasset(name, bundles[name])


class RootFactory(horus.resources.RootFactory):
    __name__ = ''
    __parent__ = None

    def __getitem__(self, key):
        child = None

        if key == 'api':
            child = APIFactory(self.request)
            child.__name__ = 'api'

        if key == 'app':
            child = app.AppController(self.request)
            child.__name__ = 'app'

        if child is not None:
            child.__parent__ = self
            return child

        raise KeyError


class APIFactory(horus.resources.BaseFactory):
    __name__ = 'api'
    __parent__ = None

    def __init__(self, request):
        super(APIFactory, self).__init__(request)

        if not 'x-annotator-auth-token' in request.headers:
            token = None

            if 'access_token' in request.params:
                token = request.params['access_token']
            elif request.user:
                token = api.token(request)

            if token:
                request.headers['x-annotator-auth-token'] = token


def includeme(config):
    config.add_route('embed', '/embed.js')
    config.add_route('index', '/', factory=RootFactory)
    add_webassets(config)
