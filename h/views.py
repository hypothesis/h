__all__ = [
    'BaseController',

    'AuthController',
    'ForgotPasswordController',
    'RegisterController',
]

from pyramid import httpexceptions
from pyramid.view import view_config, view_defaults
from pyramid.traversal import find_resource

from horus.views import (
    AuthController,
    BaseController,
    ForgotPasswordController,
    RegisterController
)

from h import interfaces

import json
import logging
log = logging.getLogger(__name__)


class BaseController(BaseController):
    def __init__(self, request):
        super(BaseController, self).__init__(request)
        getUtility = request.registry.getUtility
        self.Consumer = getUtility(interfaces.IConsumerClass)
        self.Store = getUtility(interfaces.IStoreClass)


@view_config(layout='site', renderer='templates/home.pt', route_name='index')
def home(request):
    return find_resource(request.context, '/app').embed


@view_defaults(context='h.resources.Annotation', layout='site')
class Annotation(BaseController):
    @view_config(accept='text/html', renderer='templates/displayer.pt')
    def __html__(self):
        request = self.request
        context = request.context
        if len(context) == 0:
            raise httpexceptions.HTTPNotFound(
                body_template=
                "Either no annotation exists with this identifier, or you "
                "don't have the permissions required for viewing it."
            )

        d = context._url_values()
        d['annotation'] = context
        d['annotation']['referrers'] = json.dumps(context.referrers)

        if context.get('references', []):
            root = context.__parent__[context['references'][0]]
            d['quote'] = root.quote
        else:
            d['quote'] = context.quote
            context['references'] = []

        if not 'deleted' in context:
            context['deleted'] = False

        context['date'] = context['updated']

        return d

    @view_config(accept='application/json', renderer='json')
    def __call__(self):
        request = self.request
        request.response.content_type = 'application/json'
        request.response.charset = 'UTF-8'
        return request.context

@view_defaults(context='h.resources.Streamer', layout='site')
class Streamer(BaseController):
    @view_config(accept='text/html', renderer='templates/streamer.pt')
    def __html__(self):
        return self.request.context

    @view_config(accept='application/json', renderer='json')
    def __call__(self):
        request = self.request
        request.response.content_type = 'application/json'
        request.response.charset = 'UTF-8'
        return request.context

@view_defaults(context='h.resources.UserStream', layout='site')
class UserStream(BaseController):
    @view_config(accept='text/html', renderer='templates/userstream.pt')
    def __html__(self):
        request = self.request
        context = request.context
        if context['user_count'] == 0:
            raise httpexceptions.HTTPNotFound(
                body_template=
                "No such user exists."
            )
        return context


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
