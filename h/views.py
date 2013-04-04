__all__ = [
    'BaseController',

    'AuthController',
    'ForgotPasswordController',
    'RegisterController',
]
from pyramid.traversal import find_resource
from h.displayer import DisplayerTemplate as Displayer
from h import models

from annotator.annotation import Annotation

import logging
log = logging.getLogger(__name__)

from horus.views import (
    AuthController,
    BaseController,
    ForgotPasswordController,
    RegisterController
)


@view_config(layout='site', renderer='templates/home.pt', route_name='index')
def home(request):
    return find_resource(request.context, '/app').embed

@view_config(route_name='displayer',
             renderer='h:templates/displayer.pt',
             layout='lay_displayer')
def displayer(context, request):
    #Obtain user to authorize from context token.
    if context.token:
        request.headers['x-annotator-auth-token'] = context.token
        user = auth.Authenticator(models.Consumer.get_by_key).request_user(request)
    else: user = None
        
    uid = request.matchdict['uid'] 
    annotation = Annotation.fetch_auth(user, uid)
    if not annotation : 
        raise httpexceptions.HTTPNotFound()

    if 'Content-Type' in request.headers and request.headers['Content-Type'].lower() == 'application/json' :
        res = json.dumps(annotation, indent=None if request.is_xhr else 2)
        return Response(res, content_type = 'application/json')
    else :
        try:
            #Load original quote for replies
            if 'thread' in annotation :
                original = Annotation.fetch_auth(user, annotation['thread'].split('/')[0])
            else: original = None
            replies = Annotation.search_auth(user, thread = annotation['id'])
            return Displayer(annotation, replies, original).generate_dict()        
        except e:
            log.info(str(e))
            raise httpexceptions.HTTPInternalServerError()

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
