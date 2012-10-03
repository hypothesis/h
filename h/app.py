import re

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


@view_defaults(context='h.resources.AppFactory', renderer='json')
class AppController(views.BaseController):
    ajax_options = """{
      target: null,
      success: authSuccess
    }"""

    def __init__(self, request):
        super(AppController, self).__init__(request)

        if request.method == 'POST':
            request.add_response_callback(self._handle_redirects)

    @view_config(name='auth')
    def auth(self):
        request = self.request
        context = request.context
        action = request.params.get('action', 'login')
        controller = AuthController(request)

        form = controller.form
        form.action = request.resource_path(context, 'auth', action)
        form.formid = 'auth'
        form.use_ajax = True
        form.ajax_options = self.ajax_options

        if request.method == 'POST' and request.view_name == 'auth':
            result = getattr(controller, action)()
            if isinstance(result, dict):
                if 'errors' in result:
                    result['errors'] = [str(e) for e in result['errors']]
            else:
                return result
            return dict(auth=result)

        lm = request.layout_manager
        lm.layout.add_form(form)

        return dict(auth={'form': form.render()})

    @view_config(name='register')
    def register(self):
        request = self.request
        context = request.context
        action = request.params.get('action', 'login')
        controller = RegisterController(request)

        form = controller.form
        form.action = request.resource_path(context, 'register', action)
        form.formid = 'register'
        form.use_ajax = True
        form.ajax_options = self.ajax_options

        if request.method == 'POST' and request.view_name == 'register':
            result = controller.register()
            if isinstance(result, dict):
                if 'errors' in result:
                    result['errors'] = [str(e) for e in result['errors']]
            else:
                return result
            return dict(register=result)

        lm = request.layout_manager
        lm.layout.add_form(form)

        return dict(register={'form': form.render()})

    @view_config(name='password')
    def password(self):
        request = self.request
        context = request.context
        action = request.params.get('action', 'forgot')
        controller = ForgotPasswordController(request)

        if action == 'forgot':
            schema = request.registry.getUtility(IHorusForgotPasswordSchema)
            form = request.registry.getUtility(IHorusForgotPasswordForm)
        elif action == 'reset':
            schema = request.registry.getUtility(IHorusResetPasswordSchema)
            form = request.registry.getUtility(IHorusResetPasswordForm)
        else:
            raise HTTPBadRequest()

        schema = schema().bind(request=self.request)
        form = form(schema)

        form.action = request.resource_path(context, 'password', action)
        form.formid = 'password'
        form.use_ajax = True
        form.ajax_options = self.ajax_options

        if request.method == 'POST' and request.view_name == 'password':
            result = getattr(controller, '%s_password' % action)()
            if isinstance(result, dict):
                if 'errors' in result:
                    result['errors'] = [str(e) for e in result['errors']]
            else:
                return result
            return dict(register=result)

        lm = request.layout_manager
        lm.layout.add_form(form)

        return dict(password={'form': form.render()})

    @view_config(name='persona')
    def persona(self):
        request = self.request
        schema = schemas.PersonaSchema().bind(request=request)

        form = deform.Form(schema)
        form.action = request.view_name or 'persona'
        form.formid = 'persona'
        form.use_ajax = True
        form.ajax_options = self.ajax_options

        persona = dict(id=0 if self.request.user else -1)
        try:
            if request.method == 'POST' and request.view_name == 'persona':
                persona = form.validate(request.POST.items())
                if persona.get('id', None) == -1:
                    controller = AuthController(request)
                    return controller.logout()
                else:
                    # TODO: multiple personas
                    persona = None
        except deform.exception.ValidationFailure as e:
            form = e

        lm = request.layout_manager
        lm.layout.add_form(form)

        if persona:
            return dict(persona={'form': form.render(persona)})
        else:
            return dict(persona={'form': form.render()})

    def _handle_redirects(self, request, response):
        if isinstance(response, HTTPRedirection):
            response.location = request.resource_path(request.context)
        return response

    @view_config(renderer='h:templates/app.pt')
    @view_config(renderer='json', xhr=True)
    def __call__(self):
        request = self.request
        result = {}

        for name in ['auth', 'password', 'persona', 'register']:
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
