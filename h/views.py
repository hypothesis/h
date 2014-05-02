# -*- coding: utf-8 -*-
import json
import logging

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
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config, view_defaults

from h import interfaces
from h.models import _
from h.streamer import url_values_from_document
from h.events import LoginEvent, LogoutEvent, RegistrationActivatedEvent

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


class BaseController(horus.views.BaseController):
    # pylint: disable=too-few-public-methods

    def __init__(self, request):
        super(BaseController, self).__init__(request)
        getUtility = request.registry.getUtility
        self.Consumer = getUtility(interfaces.IConsumerClass)
        self.Store = getUtility(interfaces.IStoreClass)


@view_config(
    accept='application/json',
    context='pyramid.exceptions.BadCSRFToken',
    renderer='json',
)
def bad_csrf_token(request):
    return {
        'status': 'failure',
        'reason': 'Something is wrong. Please try again.'
    }


@view_config(name='embed.js', renderer='templates/embed.txt')
@view_config(accept='application/javascript', path_info=r'^/app/embed.js$',
             name='app', renderer='templates/embed.txt')  # XXX: Deprecated
@view_config(accept='text/html', layout='sidebar',
             name='app', renderer='templates/app.pt')
@view_config(renderer='templates/help.pt', route_name='help')
@view_config(renderer='templates/home.pt', route_name='index')
def page(context, request):
    return {}


@view_defaults(context='h.models.Annotation', layout='annotation')
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

        referrers = self.Store(request).search(references=context['id'])
        d['annotation']['referrers'] = referrers

        if context.get('references', []):
            parent = context.__parent__[context['references'][-1]]
            d['quoteSource'] = 'annotation'
            d['quoteUser'] = parent['user']
            d['quote'] = parent['text']
        else:
            d['quoteSource'] = 'document'
            d['quote'] = context.quote
            context['references'] = []

        if not 'deleted' in context:
            context['deleted'] = False

        context['date'] = context['updated']

        return {'annotation': json.dumps(d)}

    @view_config(accept='application/json', renderer='json')
    def __call__(self):
        return self.request.context


@view_defaults(accept='application/json', name='app', renderer='json')
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

        if isinstance(result, dict) is False:
            if self.request.user:
                event = LoginEvent(self.request, self.request.user)
                self.request.registry.notify(event)

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

            if user:
                user.password = appstruct['password']
                self.db.add(user)
                self.db.delete(activation)
                FlashMessage(request, self.Str.authenticated, kind='success')
                event = RegistrationActivatedEvent(request, user, activation)
                request.registry.notify(event)
            else:
                form.error = colander.Invalid(
                    form.schema,
                    _('This activation code is not valid.')
                )
                result = dict(form=form.render(), errors=[form.error])

        return self.respond(result)

    @view_config(request_method='POST', request_param='__formid__=forgot')
    def forgot(self):
        controller = ForgotPasswordController(self.request)

        # XXX: Horus currently has a bug where the Activation model isn't
        # flushed before the email is generated, causing the link to be
        # broken (hypothesis/h#1156).
        #
        # Fixed in horus@90f838cef12be249a9e9deb5f38b37151649e801
        def get_activation():
            activation = self.Activation()
            self.db.add(activation)
            self.db.flush()
            return activation

        controller.Activation = get_activation
        result = controller.forgot_password()

        return self.respond(result)

    @view_config(request_method='POST', request_param='__formid__=logout')
    def logout(self):
        result = AuthController(self.request).logout()
        event = LogoutEvent(self.request)
        self.request.registry.notify(event)
        return self.respond(result)

    def respond(self, result):
        errors = isinstance(result, dict) and result.pop('errors', []) or []
        if len(errors):
            for e in errors:
                if isinstance(e, colander.Invalid):
                    msgs = e.messages()
                else:
                    msgs = [str(e)]
                for m in msgs:
                    FlashMessage(self.request, m, kind='error')
            return self(status='failure',
                        reason=_('Your submission is invalid. '
                                 'Please try again.'))
        else:
            return self()

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

    @view_config(http_cache=0)
    def __call__(self, status='okay', reason=None):
        request = self.request

        result = {
            'status': status,
            'flash': self.pop_flash(),
            'model': {
                'persona': request.context.persona,
                'personas': request.context.personas,
            },
        }

        if reason:
            result.update(reason=reason)

        return result


@view_config(
    context='h.interfaces.IStreamResource',
    layout='stream',
    renderer='templates/streamsearch.pt',
)
def stream(context, request):
    stream_type = context.get('stream_type')
    stream_key = context.get('stream_key')
    query = None

    if stream_type == 'user':
        query = {'user': stream_key}
    elif stream_type == 'tag':
        query = {'tags': stream_key}

    if query is not None:
        location = request.resource_url(context, 'stream', query=query)
        return HTTPFound(location=location)
    else:
        return context


def includeme(config):
    config.include('pyramid_chameleon')

    config.include('h.assets')
    config.include('h.forms')
    config.include('h.layouts')
    config.include('h.panels')
    config.include('h.schemas')
    config.include('h.subscribers')

    config.add_route('index', '/')
    config.add_route('help', '/docs/help')

    config.scan(__name__)
