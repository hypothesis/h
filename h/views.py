import json

from horus import (
    IHorusLoginSchema, LoginSchema,
    IHorusRegisterSchema, RegisterSchema,
    IHorusForgotPasswordSchema, ForgotPasswordSchema,
    IHorusResetPasswordSchema, ResetPasswordSchema,
    IHorusProfileSchema, ProfileSchema,

    IHorusLoginForm, IHorusRegisterForm, IHorusForgotPasswordForm,
    IHorusResetPasswordForm, IHorusProfileForm,

    SubmitForm
)
from horus.views import BaseController

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
        'horus.views.AuthController',
        attr='logout',
        route_name='horus_logout'
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
        'horus.views.RegisterController',
        attr='activate',
        renderer='h:templates/auth.pt',
        route_name='horus_activate'
    )

    config.add_view(
        'horus.views.ProfileController',
        attr='profile',
        renderer='h:templates/auth.pt',
        route_name='horus_profile'
    )

    schemas = [
        (IHorusLoginSchema, LoginSchema),
        (IHorusRegisterSchema, RegisterSchema),
        (IHorusForgotPasswordSchema, ForgotPasswordSchema),
        (IHorusResetPasswordSchema, ResetPasswordSchema),
        (IHorusProfileSchema, ProfileSchema)
    ]
    forms = [
        IHorusLoginForm, IHorusRegisterForm, IHorusForgotPasswordForm,
        IHorusResetPasswordForm, IHorusProfileForm
    ]
    for iface, schema in schemas:
        if not config.registry.queryUtility(iface):
            config.registry.registerUtility(schema, iface)
    for form in forms:
        if not config.registry.queryUtility(form):
            config.registry.registerUtility(SubmitForm, form)

    config.scan(__name__)
