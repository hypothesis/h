from functools import partial
import json

from deform import Form

from pyramid.renderers import render
from pyramid.response import Response
from pyramid.view import view_config

from pyramid_deform import FormView

@view_config(http_cache=(0, { 'must-revalidate': True}),
             renderer='h:templates/embed.pt', route_name='embed')
def embed(request, standalone=True):
    if standalone:
        request.response.content_type = 'application/javascript'
        request.response.charset = 'UTF-8'
    return {
        pkg: json.dumps(request.webassets_env[pkg].urls())
        for pkg in ['easyXDM', 'injector', 'inject_css', 'jquery']
    }

class FormView(FormView):
    """Base class for form views that adds additional capabilities to forms.

    Primarily, this passes any keyword arguments received by the constructor
    to the form class. This addition allows customizing a form slightly at
    instantiation time, such as based on request parameters or session state.
    Perhaps this should be merged into pyramid_deform.

    """

    def __init__(self, request, **kwargs):
        super(FormView, self).__init__(request)
        self.form_class = partial(self.form_class, **kwargs)

    def partial(self):
        result = self()
        if isinstance(result, dict):
            return result['form']
        else:
            return result

@view_config(renderer='templates/home.pt', route_name='home')
def home(request):
    return {
        'embed': render('h:templates/embed.pt', embed(request, False), request)
    }

def includeme(config):
    config.include('deform_bootstrap')
    config.include('pyramid_deform')

    config.add_static_view('h/sass', 'h:sass')
    config.add_static_view('h/js', 'h:js')
    config.add_static_view('h/images', 'h:images')

    config.scan(__name__)
