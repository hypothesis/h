# -*- coding: utf-8 -*-
import json
import logging

import colander
import deform
from horus import views
from horus.lib import FlashMessage
from pyramid import httpexceptions
from pyramid.view import view_config, view_defaults

from h import events, interfaces
from h.models import _
from h.streamer import url_values_from_document

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


def ajax_form(request, result):
    errors = []

    if isinstance(result, httpexceptions.HTTPRedirection):
        request.response.headers.extend(result.headers)
        result = {'status': 'okay'}
    elif isinstance(result, httpexceptions.HTTPError):
        request.response.status_code = result.code
        result = {'status': 'failure', 'reason': str(result)}
    else:
        errors = result.pop('errors', [])
        if errors:
            request.response.status_code = 400
            result['status'] = 'failure'
            result['reason'] = _('Please check your input.')
        else:
            result['status'] = 'okay'

    for e in errors:
        if isinstance(e, colander.Invalid):
            result.setdefault('errors', {})
            result['errors'].update(e.asdict())

    return result


def pop_flash(request):
    session = request.session

    queues = {
        name[3:]: [msg for msg in session.pop_flash(name[3:])]
        for name in session.keys()
        if name.startswith('_f_')
    }

    # Deal with bag.web.pyramid.flash_msg style mesages
    for msg in queues.pop('', []):
        q = getattr(msg, 'kind', '')
        msg = getattr(msg, 'plain', msg)
        queues.setdefault(q, []).append(msg)

    return queues


def model(request):
    session = request.session
    return dict(personas=session.get('personas', []))


class AsyncFormViewMapper(object):
    def __init__(self, **kw):
        self.attr = kw['attr']

    def __call__(self, view):
        def wrapper(context, request):
            if request.method == 'POST':
                data = request.json_body
                data.update(request.params)
                request.content_type = 'application/x-www-form-urlencoded'
                request.POST.clear()
                request.POST.update(data)
            inst = view(request)
            meth = getattr(inst, self.attr)
            result = meth()
            result = ajax_form(request, result)
            result['flash'] = pop_flash(request)
            result['model'] = model(request)
            result.pop('form', None)
            return result
        return wrapper


@view_config(accept='application/json',  name='app', renderer='json')
def app(request):
    return dict(status='okay', flash=pop_flash(request), model=model(request))


@view_config(accept='application/json', renderer='json',
             context='pyramid.exceptions.BadCSRFToken')
def bad_csrf_token(context, request):
    reason = _('Session is invalid.')
    result = httpexceptions.HTTPBadRequest(reason)
    return ajax_form(request, result)


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
class AnnotationController(views.BaseController):
    def __init__(self, request):
        super(AnnotationController, self).__init__(request)
        getUtility = request.registry.getUtility
        self.Store = getUtility(interfaces.IStoreClass)

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


@view_defaults(accept='text/html', renderer='templates/auth.pt')
@view_config(attr='login', route_name='login')
@view_config(attr='logout', route_name='logout')
class AuthController(views.AuthController):
    def login(self):
        request = self.request
        result = super(AuthController, self).login()

        if request.user:
            # XXX: Horus should maybe do this for us
            event = events.LoginEvent(request, request.user)
            request.registry.notify(event)

        return result

    def logout(self):
        request = self.request
        result = super(AuthController, self).logout()

        # XXX: Horus should maybe do this for us
        event = events.LogoutEvent(request)
        request.registry.notify(event)

        return result


@view_defaults(accept='application/json', name='app', renderer='json')
@view_config(attr='login', request_param='__formid__=login')
@view_config(attr='logout', request_param='__formid__=logout')
class AsyncAuthController(AuthController):
    __view_mapper__ = AsyncFormViewMapper


@view_defaults(accept='text/html', renderer='templates/auth.pt')
@view_config(attr='forgot_password', route_name='forgot_password')
@view_config(attr='reset_password', route_name='reset_password')
class ForgotPasswordController(views.ForgotPasswordController):
    def __init__(self, request):
        super(ForgotPasswordController, self).__init__(request)
        Activation = self.Activation
        self.Activation = self.get_activation(Activation)

    def get_activation(self, Activation):
        # XXX: Horus currently has a bug where the Activation model isn't
        # flushed before the email is generated, causing the link to be
        # broken (hypothesis/h#1156).
        #
        # Fixed in horus@90f838cef12be249a9e9deb5f38b37151649e801
        activation = Activation()
        self.db.add(activation)
        self.db.flush()
        return activation


@view_defaults(accept='application/json', name='app', renderer='json')
@view_config(attr='forgot_password', request_param='__formid__=forgot')
class AsyncForgotPasswordController(ForgotPasswordController):
    __view_mapper__ = AsyncFormViewMapper


@view_defaults(accept='text/html', renderer='templates/auth.pt')
@view_config(attr='register', route_name='register')
@view_config(attr='activate', route_name='activate')
class RegisterController(views.RegisterController):
    pass


@view_defaults(accept='application/json', name='app', renderer='json')
@view_config(attr='register', request_param='__formid__=register')
@view_config(attr='activate', request_param='__formid__=activate')
class AsyncRegisterController(RegisterController):
    __view_mapper__ = AsyncFormViewMapper

    def activate(self):
        """Activate a user and set a password given an activation code.

        This view is different from the activation view in horus because it
        does not require the user id to be passed. It trusts the activation
        code and updates the password.
        """
        request = self.request
        Str = self.Str

        schema = request.registry.getUtility(interfaces.IActivateSchema)
        schema = schema().bind(request=request)
        form = request.registry.getUtility(interfaces.IActivateForm)(schema)
        appstruct = None

        try:
            appstruct = form.validate(request.POST.items())
        except deform.ValidationFailure as e:
            return dict(errors=e.error.children)

        code = appstruct['code']
        activation = self.Activation.get_by_code(request, code)

        user = None
        if activation:
            user = self.User.get_by_activation(request, activation)

        if user is None:
            return dict(errors=[_('This activation code is not valid.')])

        user.password = appstruct['password']
        self.db.delete(activation)
        self.db.add(user)

        FlashMessage(request, Str.reset_password_done, kind='success')

        # XXX: Horus should maybe do this for us
        event = events.RegistrationActivatedEvent(request, user, activation)
        request.registry.notify(event)

        return {}


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
        return httpexceptions.HTTPFound(location=location)
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

    config.include('horus')

    config.add_route('index', '/')
    config.add_route('help', '/docs/help')

    config.scan(__name__)
