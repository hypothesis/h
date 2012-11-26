import re

from horus import resources

from pyramid.decorator import reify
from pyramid.interfaces import ILocation

from webassets import Bundle
from webassets.filter import register_filter
from webassets.loaders import PythonLoader

from zope.interface import implementer

from h import api, models

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
    Bundle('deform_bootstrap:static/bootstrap.min.js'),
    Bundle(
        Bundle(
            Bundle(
                'h:js/src/deform.coffee',
                debug=False,
                filters='coffeescript',
                output='js/deform.js',
            ),
            Bundle(
                'h:js/src/app.coffee',
                debug=False,
                filters='coffeescript',
                output='js/app.js',
            ),
            Bundle(
                'h:js/src/controllers.coffee',
                debug=False,
                filters='coffeescript',
                output='js/controllers.js',
            ),
            Bundle(
                'h:js/src/directives.coffee',
                debug=False,
                filters='coffeescript',
                output='js/directives.js',
            ),
            Bundle(
                'h:js/src/services.coffee',
                debug=False,
                filters='coffeescript',
                output='js/services.js',
            ),
            filters='uglifyjs',
            output='js/hypothesis.min.js'
        ),
        Bundle(
            Bundle(
                'h:js/src/plugin/heatmap.coffee',
                debug=False,
                filters='coffeescript',
                output='js/lib/annotator.heatmap.js',
            ),
            filters='uglifyjs',
            output='js/lib/annotator.heatmap.min.js'
        ),
        output='js/hypothesis-full.min.js',
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

#
# Application dependencies
#

angular = Bundle('h:js/lib/angular.min.js')
d3 = Bundle('h:js/lib/d3.v2.min.js')
easyXDM = Bundle('h:js/lib/easyXDM.min.js')
handlebars = Bundle('h:js/lib/handlebars-runtime.min.js')
jquery = Bundle('deform:static/scripts/jquery-1.7.2.min.js')
jwz = Bundle('h:js/lib/jwz.min.js')

deform = Bundle(
    jquery,
    Bundle(
        'deform:static/scripts/jquery.form-3.09.js',
        'deform:static/scripts/deform.js',
    )
)

# PageDown is used to render Markdown-formatted text to HTML
pagedown = Bundle(
    Bundle(
        'h:js/lib/Markdown.Converter.js',
        'h:js/lib/Markdown.Sanitizer.js',
    ),
    filters='uglifyjs',
    output='js/markdown.min.js',
)
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


class WebassetsResourceRegistry(object):
    def __init__(self, environment):
        self.environment = environment

    def __call__(self, requirements):
        result = {'js': [], 'css': []}
        for requirement, _version in requirements:
            if not requirement in self.environment:
                continue
            bundle = self.environment[requirement]
            for source in bundle.urls():
                for thing in ('js', 'css'):
                    if re.search(r'/[^/?]+\.%s\??[^/]*$' % thing, source):
                        if not source in result[thing]:
                            result[thing].append(source)
        return result


@implementer(ILocation)
class BaseResource(resources.BaseFactory):
    """Base Resource class from which all resources are derived"""

    __name__ = None
    __parent__ = None


class InnerResource(BaseResource):
    """Helper Resource class for declarative, traversal-based routing

    Classes which inherit from this should contain attributes which are either
    class constructors for classes whose instances provide the
    :class:`pyramid.interfaces.ILocation` interface else attributes which are,
    themselves, instances of such a class. Such attributes are treated as
    valid traversal children of the Resource whose path component is the name
    of the attribute.
    """

    def __getitem__(self, name):
        """
        Any class attribute which is an instance providing
        :class:`pyramid.interfaces.ILocation` will be returned as is.

        Attributes which are constructors for implementing classes will
        be replaced with a constructed instance by reifying the newly
        constructed resource in place of the attribute.

        Assignment to the sub-resources `__name__` and `__parent__` properties
        is handled automatically.
        """

        factory_or_resource = getattr(self, name, None)

        if factory_or_resource:
            if ILocation.implementedBy(factory_or_resource):
                inst = factory_or_resource(self.request)
                inst.__name__ = name
                inst.__parent__ = self
                setattr(self, name, inst)
                return inst

            if ILocation.providedBy(factory_or_resource):
                return factory_or_resource

        raise KeyError(name)


class RootFactory(InnerResource, resources.RootFactory):
    pass


class APIFactory(InnerResource):
    def __init__(self, request):
        super(APIFactory, self).__init__(request)

        if not 'x-annotator-auth-token' in request.headers:
            if 'access_token' in request.params:
                token = request.params['access_token']
                request.headers['x-annotator-auth-token'] = token


class AppFactory(BaseResource):
    def __init__(self, request):
        super(AppFactory, self).__init__(request)

    @reify
    def persona(self):
        request = self.request

        # Transition code until multiple sign-in is implemented
        if request.user:
            return {
                'username': request.user.username,
                'provider': request.host,
            }

        return None

    @reify
    def personas(self):
        request = self.request

        # Transition code until multiple sign-in is implemented
        if request.user:
            return [self.persona]

        return []

    @reify
    def consumer(self):
        settings = self.request.registry.settings
        key = settings['api.key']
        secret = settings.get('api.secret')
        if not secret:
            consumer = models.Consumer.get_by_key(key)
        else:
            consumer = models.Consumer(key=key, secret=secret)
        assert(consumer)
        return consumer

    @reify
    def token(self):
        if not self.persona:
            return None

        message = {
            'userId': 'acct:%(username)s@%(provider)s' % self.persona,
            'consumerKey': str(self.consumer.key),
            'ttl': self.consumer.ttl,
        }
        return api.auth.encode_token(message, self.consumer.secret)


def includeme(config):
    config.include('horus.routes')
    config.include('pyramid_webassets')

    RootFactory.api = APIFactory
    RootFactory.app = AppFactory

    config.add_route('embed', '/embed.js')
    config.add_route('index', '/', factory='h.resources.RootFactory')

    loader = PythonLoader(__name__)
    bundles = loader.load_bundles()
    for name in bundles:
        config.add_webasset(name, bundles[name])

    from deform.field import Field
    resource_registry = WebassetsResourceRegistry(config.get_webassets_env())
    Field.set_default_resource_registry(resource_registry)
