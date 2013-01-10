import colander
import deform

from pyramid.decorator import reify
from pyramid.view import view_config, view_defaults

from h import exceptions, interfaces, messages, views
from h.messages import _


@view_defaults(context='h.resources.AppFactory', layout='app', renderer='json')
class AppController(views.BaseController):
    @reify
    def auth_controller(self):
        return views.AuthController(self.request)

    @reify
    def forgot_controller(self):
        return views.ForgotPasswordController(self.request)

    @reify
    def register_controller(self):
        return views.RegisterController(self.request)

    @reify
    def login_form(self):
        return self.auth_controller.form

    @reify
    def register_form(self):
        return self.register_controller.form

    @reify
    def forgot_form(self):
        request = self.request
        schema = request.registry.getUtility(interfaces.IForgotPasswordSchema)
        schema = schema().bind(request=self.request)
        form = request.registry.getUtility(interfaces.IForgotPasswordForm)
        form = form(schema)
        return form

    @reify
    def reset_form(self):
        request = self.request
        schema = request.registry.getUtility(interfaces.IResetPasswordSchema)
        schema = schema().bind(requeppst=self.request)
        form = request.registry.getUtility(interfaces.IResetPasswordForm)
        form = form(schema)
        return form

    @reify
    def activate_form(self):
        request = self.request
        schema = request.registry.getUtility(interfaces.IActivateSchema)
        schema = schema().bind(request=self.request)
        form = request.registry.getUtility(interfaces.IActivateForm)
        form = form(schema)
        return form

    @view_config(request_method='POST', request_param='__formid__=login')
    def login(self):
        request = self.request
        form = self.login_form

        try:
            appstruct = form.validate(request.POST.items())
        except deform.ValidationFailure as e:
            return {
                'status': 'failure',
                'reason': messages.INVALID_FORM,
                'error': e.error.asdict(),
            }

        try:
            user = self.auth_controller.check_credentials(
                appstruct['username'],
                appstruct['password'],
            )
        except exceptions.AuthenticationFailure as e:
            return {
                'status': 'failure',
                'reason': str(e),
            }

        request.user = user

        result = request.context.__json__()
        result.update(status='okay')
        return result

    @view_config(request_method='POST', request_param='__formid__=register')
    def register(self):
        request = self.request
        form = self.register_form

        try:
            appstruct = form.validate(request.POST.items())
        except deform.ValidationFailure as e:
            return {
                'status': 'failure',
                'reason': messages.INVALID_FORM,
                'error': e.error.asdict(),
            }

        try:
            user = self.register_controller.create_user(
                appstruct['email'],
                appstruct['username'],
                appstruct['password'],
            )
        except exceptions.RegistrationFailure as e:
            return {
                'status': 'failure',
                'reason': str(e)
            }

        if request.registry.settings.get('horus.autologin', False):
            self.db.flush()  # to get the id
            request.user = user

        result = request.context.__json__()
        result.update(status='okay')
        return result

    @view_config(request_method='POST', request_param='__formid__=activate')
    def activate(self):
        request = self.request
        form = self.activate_form

        appstruct = None
        try:
            appstruct = form.validate(request.POST.items())
        except deform.ValidationFailure as e:
            return {
                'status': 'failure',
                'reason': messages.INVALID_FORM,
                'error': e.error.asdict(),
            }
        else:
            code = appstruct['code']
            activation = self.Activation.get_by_code(request, code)
            if activation:
                user = self.User.get_by_activation(request, activation)

                if user:
                    user.set_password(appstruct['Password'])
                    self.db.add(user)
                    self.db.delete(activation)
            else:
                form.error = colander.Invalid(
                    form.schema,
                    _('This activation code is not valid.')
                )
                return {
                    'status': 'failure',
                    'reason': messages.INVALID_FORM,
                    'error': e.error.asdict(),
                }

        result = request.context.__json__()
        result.update(status='okay')
        return result

    @view_config(request_method='POST', request_param='__formid__=forgot')
    def forgot(self):
        request = self.request
        form = self.forgot_form

        result = self.forgot_controller.forgot_password()
        if isinstance(result, dict):
            if 'errors' in result:
                error = colander.Invalid(form.schema, messages.INVALID_FORM)
                return {
                    'status': 'failure',
                    'reason': messages.INVALID_FORM,
                    'error': error.asdict(),
                }
        result = request.context.__json__()
        result.update(status='okay')
        return result

    @view_config(name='logout')
    def logout(self):
        request = self.request

        self.auth_controller.logout()
        request.user = None

        result = request.context.__json__()
        result.update(status='okay')
        return result

    @view_config(name='embed.js', renderer='templates/embed.txt')
    def embed(self):
        request = self.request
        request.response.content_type = 'application/javascript'
        request.response.charset = 'UTF-8'
        return request.context.embed

    @view_config(renderer='json', xhr=True)
    def __call__(self):
        request = self.request
        return request.context

    @view_config(renderer='h:templates/app.pt')
    def __html__(self):
        request = self.request
        request.session.new_csrf_token()
        return {}


def includeme(config):
    config.scan(__name__)
