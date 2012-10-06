import colander
import deform

from horus.views import (
    AuthController,
    ForgotPasswordController,
    RegisterController
)

from horus import (
    IHorusForgotPasswordForm,
    IHorusResetPasswordForm,
    IHorusForgotPasswordSchema,
    IHorusResetPasswordSchema
)

from pyramid.httpexceptions import HTTPBadRequest, HTTPRedirection
from pyramid.view import view_config, view_defaults

from h import schemas, views
from h.messages import _


@view_defaults(context='h.resources.AppFactory', renderer='json')
class AppController(views.BaseController):
    ajax_options = """{
      target: null,
      success: afterRequest
    }"""

    def __init__(self, request):
        super(AppController, self).__init__(request)

        if request.method == 'POST':
            request.add_response_callback(self._handle_redirects)

    @view_config(request_param='__formid__=auth')
    def auth(self):
        request = self.request
        context = request.context
        action = request.params.get('action', 'login')

        if action not in ['login', 'logout']:
            raise HTTPBadRequest()

        controller = AuthController(request)
        form = controller.form
        form.formid = 'auth'
        form.use_ajax = True
        form.ajax_options = self.ajax_options

        if request.POST.get('__formid__', '') == 'auth':
            result = getattr(controller, action)()
            error = request.session.pop_flash('error')
            if isinstance(result, dict):
                if error:
                    form.error = colander.Invalid(form.schema, error[0])
                    result = {'form': form.render()}
            else:
                return result
            return dict(auth=result)

        lm = request.layout_manager
        lm.layout.add_form(form)

        return dict(auth={'form': form.render()})

    @view_config(request_param='__formid__=register')
    def register(self):
        request = self.request
        context = request.context
        action = request.params.get('action', 'register')

        if action not in ['register', 'activate']:
            raise HTTPBadRequest()

        controller = RegisterController(request)
        form = controller.form
        form.formid = 'register'
        form.use_ajax = True
        form.ajax_options = self.ajax_options

        if request.POST.get('__formid__', '') == 'register':
            result = getattr(controller, action)()
            error = request.session.pop_flash('error')
            if isinstance(result, dict):
                if error:
                    form.error = colander.Invalid(form.schema, error[0])
                    result = {'form': form.render()}
            else:
                return result
            return dict(register=result)

        lm = request.layout_manager
        lm.layout.add_form(form)

        return dict(register={'form': form.render()})

    @view_config(request_param='__formid__=reset')
    def reset(self):
        request = self.request
        context = request.context

        schema = schemas.SecurityCodeSchema().bind(request=self.request)
        form = deform.Form(schema, buttons=('Log in',))

        form.formid = 'reset'
        form.use_ajax = True
        form.ajax_options = self.ajax_options

        if request.POST.get('__formid__', '') == 'reset':
            # if isinstance(result, dict):
            #     if 'errors' in result:
            #         result['errors'] = [str(e) for e in result['errors']]
            # else:
            #     return result
            return dict(reset=result)

        lm = request.layout_manager
        lm.layout.add_form(form)

        return dict(reset={'form': form.render()})

    @view_config(request_param='__formid__=password')
    def password(self):
        request = self.request
        context = request.context
        action = request.params.get('action', 'forgot')

        if action == 'forgot':
            schema = request.registry.getUtility(IHorusForgotPasswordSchema)
            form = request.registry.getUtility(IHorusForgotPasswordForm)
        elif action == 'reset':
            schema = request.registry.getUtility(IHorusResetPasswordSchema)
            form = request.registry.getUtility(IHorusResetPasswordForm)
        else:
            raise HTTPBadRequest()

        controller = ForgotPasswordController(request)
        schema = schema().bind(request=self.request)
        form = form(schema)

        form.formid = 'password'
        form.use_ajax = True
        form.ajax_options = self.ajax_options

        if request.POST.get('__formid__', '') == 'password':
            result = getattr(controller, '%s_password' % action)()
            error = request.session.pop_flash('error')
            if isinstance(result, dict):
                if error:
                    form.error = colander.Invalid(form.schema, error[0])
                    result = {'form': form.render()}
            else:
                return result
            return dict(password=result)

        lm = request.layout_manager
        lm.layout.add_form(form)

        return dict(password={'form': form.render()})

    @view_config(request_param='__formid__=persona')
    def persona(self):
        request = self.request
        schema = schemas.PersonaSchema().bind(request=request)

        form = deform.Form(
            schema,
            formid='persona',
            use_ajax=True,
            ajax_options=self.ajax_options
        )

        lm = request.layout_manager
        lm.layout.add_form(form)

        try:
            if request.POST.get('__formid__', '') == 'persona':
                persona = form.validate(request.POST.items())
                if persona.get('id', None) == -1:
                    controller = AuthController(request)
                    return controller.logout()
                else:
                    # TODO: multiple personas
                    persona = None
        except deform.exception.ValidationFailure as e:
            return dict(persona={'form': form.render()})
        else:
            persona = dict(id=0 if request.user else -1)
            return dict(persona={'form': form.render(persona)})

    def _handle_redirects(self, request, response):
        if isinstance(response, HTTPRedirection):
            response.location = request.resource_path(request.context)
        return response

    @view_config(renderer='h:templates/app.pt')
    @view_config(renderer='json', xhr=True)
    def __call__(self):
        request = self.request
        result = {}

        for name in ['auth', 'password', 'persona', 'register', 'reset']:
            subresult = getattr(self, name)()
            if isinstance(subresult, dict):
                result.update(subresult)
            else:
                return subresult

        result.update(
            token_url=request.resource_url(request.root, 'api', 'access_token')
        )

        return result


def includeme(config):
    config.scan(__name__)
