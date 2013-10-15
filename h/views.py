try:
    import simplejson as json
except ImportError:
    import json

import colander
import deform

import horus.views

from horus.lib import FlashMessage
from horus.views import (
    AuthController,
    ForgotPasswordController,
    RegisterController,
)

from pyramid import httpexceptions
from pyramid.traversal import find_resource
from pyramid.view import view_config, view_defaults

from h import interfaces
from h.models import _
from h.streamer import url_values_from_document

import mannord

import logging
log = logging.getLogger(__name__)


class BaseController(horus.views.BaseController):
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

@view_config(route_name='help', layout='site', renderer='templates/help.pt')
def my_view(request):
    return find_resource(request.context, '/app').embed


@view_config(context='h.resources.Annotation', route_name='upvote')
def upvote(request):
    log.info("Attention")
    log.info("INSIDE UPVOTE")


@view_defaults(context='h.resources.Annotation', layout='site')
class AnnotationController(BaseController):
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


@view_defaults(
    accept='application/json',
    context='h.resources.AppFactory',
    layout='app',
    renderer='json'
)
class AppController(BaseController):
    def __init__(self, request):
        super(AppController, self).__init__(request)

        if request.method == 'POST':
            try:
                data = request.json_body
                data.update(request.params)
            except ValueError:
                pass  # Request from legacy client or non-js browser.
            else:
                request.content_type = 'application/x-www-form-urlencoded'
                request.POST.clear()
                request.POST.update(data)

    @view_config(request_method='POST', request_param='__formid__=login')
    def login(self):
        result = AuthController(self.request).login()
        return self.respond(result)

    @view_config(request_method='POST', request_param='__formid__=register')
    def register(self):
        result = RegisterController(self.request).register()
        return self.respond(result)

    @view_config(request_method='POST', request_param='__formid__=activate')
    def activate(self):
        request = self.request
        schema = request.registry.getUtility(interfaces.IActivateSchema)
        schema = schema().bind(request=self.request)
        form = request.registry.getUtility(interfaces.IActivateForm)(schema)

        appstruct = None
        result = None
        try:
            appstruct = form.validate(request.POST.items())
        except deform.ValidationFailure as e:
            result = dict(form=e.render(), errors=e.error.children)
        else:
            code = appstruct['code']
            activation = self.Activation.get_by_code(request, code)
            user = None
            if activation:
                user = self.User.get_by_activation(request, activation)

            request.user = user
            if user:
                user.password = appstruct['password']
                self.db.add(user)
                self.db.delete(activation)
                FlashMessage(request, self.Str.authenticated, kind='success')
            else:
                form.error = colander.Invalid(
                    form.schema,
                    _('This activation code is not valid.')
                )
                result = dict(form=form.render(), errors=[form.error])

        return self.respond(result)

    @view_config(request_method='POST', request_param='__formid__=forgot')
    def forgot(self):
        result = ForgotPasswordController(self.request).forgot_password()
        return self.respond(result)

    @view_config(request_method='POST', request_param='__formid__=logout')
    def logout(self):
        result = AuthController(self.request).logout()
        self.request.user = None
        return self.respond(result)

    @view_config(name='embed.js', renderer='templates/embed.txt')
    def embed(self):
        request = self.request

        # Unless we're debugging, serve the embed with a 10 minute cache
        # to reduce server load since this is potentially fetched frequently.
        if not request.registry.settings.get('pyramid.reload_templates'):
            request.response.cache_control.max_age = 600

        # Don't leave them guessing
        request.response.content_type = 'application/javascript'
        request.response.charset = 'UTF-8'

        return request.context.embed

    def success(self):
        result = self()
        result.update(status='okay')
        return result

    def failure(self, reason):
        result = self()
        result.update(status='failure', reason=reason)
        return result

    def respond(self, result):
        errors = isinstance(result, dict) and result.pop('errors', []) or []
        if len(errors):
            for e in errors:
                if isinstance(e, colander.Invalid):
                    msgs = e.messages()
                else:
                    msgs = [str(e)]
                for m in msgs: FlashMessage(self.request, m, kind='error')
            return self.failure(_('Your submission is invalid. '
                                  'Please try again.'))
        else:
            return self.success()

    def pop_flash(self):
        session = self.request.session

        result = {
            name[3:]: [msg for msg in session.pop_flash(name[3:])]
            for name in session.keys()
            if name.startswith('_f_')
        }

        # Deal with bag.web.pyramid.flash_msg style mesages
        for msg in result.pop('', []):
            q = getattr(msg, 'kind', '')
            msg = getattr(msg, 'plain', msg)
            result.setdefault(q, []).append(msg)

        return result

    def __call__(self):
        request = self.request

        # Ensure we have a token in case this is the first request.
        # I feel this is a little bit hacky.
        request.session.get_csrf_token()

        model = {
            'token': self.Token,
            'persona': request.context.persona,
            'personas': request.context.personas,
        }

        return {
            'flash': self.pop_flash(),
            'model': model,
        }

    @view_config(http_cache=0)
    def __json__(self):
        return self.success()

    @view_config(
        accept='text/html',
        layout='sidebar',
        renderer='h:templates/app.pt'
    )
    def __html__(self):
        request = self.request
        request.session.new_csrf_token()
        return {
            'service_url': request.route_url('api', subpath=''),
            'token_url': request.route_url('token'),
        }


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
