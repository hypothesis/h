import colander
import deform

from horus.views import (
    AuthController,
    ForgotPasswordController,
    RegisterController
)

from pyramid.decorator import reify
from pyramid.httpexceptions import exception_response
from pyramid.view import view_config, view_defaults

from h import exceptions, interfaces, messages, views
from h.messages import _


@view_defaults(context='h.resources.AppFactory', renderer='json')
class AppController(views.BaseController):
    @reify
    def auth_controller(self):
        return AuthController(self.request)

    @reify
    def register_controller(self):
        return RegisterController(self.request)

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
        form.formid = 'reset'
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
                'form': {
                    'login': e.render()
                }
            }

        try:
            user = self.auth_controller.check_credentials(
                appstruct['username'],
                appstruct['password'],
            )
        except exceptions.AuthenticationFailure as e:
            form.error = colander.Invalid(form.schema, e)
            return {
                'status': 'failure',
                'reason': e.message,
                'form': {
                    'login': form.render(appstruct),
                }
            }

        request.user = user

        return {
            'status': 'okay',
            'form': {
                'login': form.render()
            },
            'model': self(),
        }

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
                'form': {
                    'login': e.render()
                }
            }

        try:
            user = self.register_controller.create_user(
                appstruct['email'],
                appstruct['username'],
                appstruct['password'],
            )
        except exceptions.RegistrationFailure as e:
            form.error = colander.Invalid(form.schema, str(e))
            return {
                'form': {
                    'register': form.render(appstruct)
                },
            }

        if request.registry.settings.get('horus.autologin', False):
            self.db.flush()  # to get the id
            request.user = user

        return {
            'form': {
                'register': form.render()
            },
            'model': self(),
        }

    @view_config(request_method='POST', request_param='__formid__=activate')
    def reset(self):
        request = self.request
        form = self.activate_form

        appstruct = None
        try:
            appstruct = form.validate(request.POST.items())
        except deform.ValidationFailure as e:
            result = {'form': e.render()}
        else:
            code = appstruct['code']
            activation = self.Activation.get_by_code(request, code)
            if activation:
                user = self.User.get_by_activation(request, activation)

                if user:
                    user.set_password(appstruct['Password'])
                    self.db.add(user)
                    self.db.delete(activation)

            form.error = colander.Invalid(
                form.schema,
                _('This activation code is not valid.')
            )

        if appstruct:
            result = {'form': form.render(appstruct)}
        else:
            result = {'form': form.render()}

        return dict(reset=result)

    @view_config(request_method='POST', request_param='__formid__=forgot')
    def forgot(self):
        request = self.request
        controller = ForgotPasswordController(request)
        form = self.forgot_form

        result = controller.forgot_password()
        error = request.session.pop_flash('error')
        if isinstance(result, dict):
            if error:
                form.error = colander.Invalid(form.schema, error[0])
                result = {'form': form.render()}
            else:
                return result
        return dict(password=result)

    @view_config(name='logout')
    def logout(self):
        self.auth_controller.logout()
        self.request.user = None

    @view_config(name='token', renderer='string')
    def token(self):
        token = self.request.context.token
        if not token:
            raise exception_response(403, detail=messages.NOT_LOGGED_IN)
        else:
            return token

    @view_config(name='model', renderer='json', xhr=True)
    def __call__(self):
        request = self.request
        model = {
            name: getattr(request.context, name)
            for name in ['persona', 'personas', 'token']
        }
        model.update(tokenURL=request.resource_url(request.context, 'token'))
        return model

    @view_config(renderer='h:templates/app.pt')
    def __html__(self):
        request = self.request

        layout = request.layout_manager.layout
        for name in ['login', 'forgot', 'register', 'activate']:
            form = getattr(self, '%s_form' % name)
            layout.add_form(form)

        token_url = request.resource_url(request.root, 'api', 'access_token')

        return {'token_url': token_url}


def includeme(config):
    config.scan(__name__)
