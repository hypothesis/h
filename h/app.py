import colander
import deform

from bag.web.pyramid.flash_msg import FlashMessage

from pyramid.view import view_config, view_defaults

from h import api, interfaces, views
from h.models import _


@view_defaults(context='h.resources.AppFactory', layout='app', renderer='json')
class AppController(views.BaseController):
    @view_config(request_method='POST', request_param='__formid__=login')
    def login(self):
        result = views.AuthController(self.request).login()
        return self.respond(result)

    @view_config(request_method='POST', request_param='__formid__=register')
    def register(self):
        result = views.RegisterController(self.request).register()
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
        result = views.ForgotPasswordController(self.request).forgot_password()
        return self.respond(result)

    @view_config(name='logout')
    def logout(self):
        result = views.AuthController(self.request).logout()
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

    @view_config(http_cache=0, name='state', renderer='json')
    def __call__(self):
        request = self.request

        # Ensure we have a token in case this is the first request.
        # I feel this is a little bit hacky.
        request.session.get_csrf_token()

        model = {
            'token': api.TokenController(request)(),
            'token_url': request.route_url('token'),
            'persona': request.context.persona,
            'personas': request.context.personas,
        }

        return {
            'flash': self.pop_flash(),
            'model': model,
        }

    @view_config(layout='sidebar', renderer='h:templates/app.pt')
    def __html__(self):
        request = self.request
        request.session.new_csrf_token()
        return {
            'service_url': self.Store(request).base_url,
        }


def includeme(config):
    config.scan(__name__)
