__all__ = [
    'BaseController',

    'AuthController',
    'ForgotPasswordController',
    'RegisterController',
]

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
from h import streamer as streamer_template

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


@view_defaults(context='h.resources.Annotation', layout='lay_displayer')
class Annotation(BaseController):
    @view_config(accept='text/html', renderer='templates/displayer.pt')
    def __html__(self):
        request = self.request
        annotation = request.context

        if len(annotation) == 0:
          raise httpexceptions.HTTPNotFound()

        d = {'annotation': annotation}
        if annotation.references:
            thread_root = annotation.references[0]
            root_annotation = annotation.__parent__[thread_root]
            d['quote'] = root_annotation.quote
        else:
            d['quote'] = annotation.quote
        d.update(annotation._url_values())
        d['fuzzy_date'] = annotation._fuzzyTime(annotation['updated'])
        d['readable_user'] = annotation._userName(annotation['user'])
        d['replies'] = annotation.replies

        #Count nested reply numbers
        replies = 0
        for reply in annotation.replies:
            if not isinstance(reply, list):
                replies = replies + reply['number_of_replies'] + 1
        d['number_of_replies'] = replies

        return d

    @view_config(accept='application/json', renderer='json')
    def __call__(self):
        request = self.request
        request.response.content_type = 'application/json'
        request.response.charset = 'UTF-8'
        return request.context

@view_defaults(context='h.resources.Streamer', layout='lay_streamer')
class Streamer(BaseController):
    @view_config(accept='text/html', renderer='templates/streamer.pt')
    def __html__(self):
        streamer = self.request.context
        return streamer

    @view_config(accept='application/json', renderer='json')
    def __call__(self):
        request = self.request
        request.response.content_type = 'application/json'
        request.response.charset = 'UTF-8'
        return request.context

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
