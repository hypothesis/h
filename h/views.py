__all__ = ['BaseController']

import json

from pyramid.renderers import render
from pyramid.view import view_config

from horus.views import BaseController


@view_config(http_cache=(0, {'must-revalidate': True}),
             renderer='templates/embed.txt', route_name='embed')
def embed(request, standalone=True):
    if standalone:
        request.response.content_type = 'application/javascript'
        request.response.charset = 'UTF-8'
    return {
        pkg: json.dumps(request.webassets_env[pkg].urls())
        for pkg in ['inject', 'jquery', 'raf']
    }


@view_config(layout='site', renderer='templates/home.pt', route_name='index')
def home(request):
    return {
        'embed': render('templates/embed.txt', embed(request, False), request)
    }


def includeme(config):
    config.add_view(
        'horus.views.AuthController',
        attr='login',
        renderer='h:templates/auth.pt',
        route_name='login'
    )

    config.add_view(
        'horus.views.AuthController',
        attr='logout',
        route_name='logout'
    )

    config.add_view(
        'horus.views.ForgotPasswordController',
        attr='forgot_password',
        renderer='h:templates/auth.pt',
        route_name='forgot_password'
    )

    config.add_view(
        'horus.views.ForgotPasswordController',
        attr='reset_password',
        renderer='h:templates/auth.pt',
        route_name='reset_password'
    )

    config.add_view(
        'horus.views.RegisterController',
        attr='register',
        renderer='h:templates/auth.pt',
        route_name='register'
    )

    config.add_view(
        'horus.views.RegisterController',
        attr='activate',
        renderer='h:templates/auth.pt',
        route_name='activate'
    )

    config.add_view(
        'horus.views.ProfileController',
        attr='profile',
        renderer='h:templates/auth.pt',
        route_name='profile'
    )

    config.scan(__name__)
