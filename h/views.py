__all__ = [
    'BaseController',

    'AuthController',
    'ForgotPasswordController',
    'RegisterController',
]

from pyramid import httpexceptions
from pyramid.view import view_config, view_defaults
from pyramid.traversal import find_resource
from pyramid import httpexceptions

from horus.views import (
    AuthController,
    BaseController,
    ForgotPasswordController,
    RegisterController
)

from h import interfaces
from h.streamer import url_values_from_document

import json
import logging
log = logging.getLogger(__name__)


class BaseController(BaseController):
    def __init__(self, request):
        super(BaseController, self).__init__(request)
        getUtility = request.registry.getUtility
        self.Consumer = getUtility(interfaces.IConsumerClass)
        self.Store = getUtility(interfaces.IStoreClass)
        self.Token = getUtility(interfaces.ITokenClass)


@view_config(
    context='h.resources.RootFactory',
    layout='site',
    renderer='templates/home.pt',
)
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

        d = url_values_from_document(context)
        d['annotation'] = context
        d['annotation']['referrers'] = context.referrers

        if context.get('references', []):
            parent = context.__parent__[context['references'][-1]]
            d['quote'] = parent['text']
        else:
            d['quote'] = context.quote
            context['references'] = []

        if not 'deleted' in context:
            context['deleted'] = False

        context['date'] = context['updated']

        return {'annotation': json.dumps(d)}

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


@view_defaults(context='h.resources.Stream', layout='site')
class Stream(BaseController):
    @view_config(accept='text/html', renderer='templates/stream.pt')
    def __html__(self):
        return self.request.context

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
