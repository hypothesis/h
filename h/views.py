import json

from pyramid.renderers import render
from pyramid.view import view_config


@view_config(http_cache=(0, {'must-revalidate': True}),
             renderer='templates/embed.txt', route_name='embed')
def embed(request, standalone=True):
    if standalone:
        request.response.content_type = 'application/javascript'
        request.response.charset = 'UTF-8'
    return {
        pkg: json.dumps(request.webassets_env[pkg].urls())
        for pkg in ['easyXDM', 'injector', 'inject_css', 'jquery']
    }


@view_config(renderer='templates/home.pt', route_name='index')
def home(request):
    return {
        'embed': render('templates/embed.txt', embed(request, False), request)
    }


def includeme(config):
    config.add_static_view('h/sass', 'h:sass')
    config.add_static_view('h/js', 'h:js')
    config.add_static_view('h/images', 'h:images')

    config.add_view(
        'horus.views.AuthController',
        attr='login',
        renderer='h:templates/auth.pt',
        route_name='horus_login'
    )

    config.add_view(
        'horus.views.ForgotPasswordController',
        attr='forgot_password',
        renderer='h:templates/auth.pt',
        route_name='horus_forgot_password'
    )

    config.add_view(
        'horus.views.ForgotPasswordController',
        attr='reset_password',
        renderer='h:templates/auth.pt',
        route_name='horus_reset_password'
    )

    config.add_view(
        'horus.views.RegisterController',
        attr='register',
        renderer='h:templates/auth.pt',
        route_name='horus_register'
    )

    config.add_view(
        'horus.views.ProfileController',
        attr='profile',
        renderer='h:templates/auth.pt',
        route_name='horus_profile'
    )

    config.scan(__name__)
