from functools import partial
import json

from pyramid.renderers import render
from pyramid.response import Response
from pyramid.view import view_config

from pyramid_deform import FormView
from pyramid_webassets import IWebAssetsEnvironment

@view_config(http_cache=(0, { 'must-revalidate': True}),
             renderer='h:templates/embed.pt', route_name='embed')
def embed(request, standalone=True):
    assets_env = request.registry.queryUtility(IWebAssetsEnvironment)
    if standalone:
        request.response.content_type = 'application/javascript'
        request.response.charset = 'UTF-8'
    return {
        pkg: json.dumps(assets_env[pkg].urls())
        for pkg in ['easyXDM', 'injector', 'inject_css', 'jquery']
    }

class FormView(FormView):
    """Base class for form views that adds additional capabilities to forms.

    Primarily, this passes any keyword arguments received by the constructor
    to the form class. This addition allows customizing a form slightly at
    instantiation time, such as based on request parameters or session state.
    Perhaps this should be merged into pyramid_deform.

    Deform comes with AJAH support in the form of `use_ajax = True` on the
    form class but this attemps to go further. Using the form id, the page should
    post back its URL with XHR and, by defining a mapping of form ids to
    form views for from the original view handler, construct pages which are
    a composite of forms.

    I'm sure there are some well tread patterns around for this. For now it's
    a sketch of an idea and a harmless base class.

    """

    use_ajax = True
    ajax_options = json.dumps({
        'type': 'POST'
    })

    def __init__(self, request, **kwargs):
        super(FormView, self).__init__(request)
        self.form_class = partial(self.form_class, **kwargs)

    def __call__(self):
        result = super(FormView, self).__call__()
        if self.request.is_xhr:
            if isinstance(result, Response):
                raise result
            return result['form']
        else:
            return result

    @property
    def partial(self):
        return getattr(self, self.request.params['__formid__'])

@view_config(renderer='templates/home.pt', route_name='home')
def home(request):
    assets_env = request.registry.queryUtility(IWebAssetsEnvironment)
    return {
        'css_links': assets_env['site_css'].urls(),
        'embed': render('h:templates/embed.pt', embed(request, False), request)
    }

def includeme(config):
    config.include('deform_bootstrap')
    config.include('pyramid_deform')

    config.add_static_view('h/sass', 'h:sass')
    config.add_static_view('h/js', 'h:js')
    config.add_static_view('h/images', 'h:images')

    config.scan(__name__)
