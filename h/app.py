import deform

import horus.views
from horus.views import BaseController

from pyramid.httpexceptions import HTTPRedirection
from pyramid.view import view_config, view_defaults

from h import schemas


@view_defaults(context='h.app.AppController', renderer='json')
class AppController(BaseController):
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
        lm = request.layout_manager
        action = request.params.get('action')

        if action == 'activate' or action == 'register':
            controller = horus.views.RegisterController(request)
        else:
            action = 'login'
            controller = horus.views.AuthController(request)

        form = controller.form
        form.action = '%s?action=%s' % (request.view_name or 'auth', action)
        form.formid = 'auth'
        form.use_ajax = True
        form.ajax_options = self.ajax_options
        lm.layout.add_form('auth', form)

        if request.method == 'POST':
            if request.view_name == 'auth':
                result = getattr(controller, action)()
                if isinstance(result, dict):
                    if 'errors' in result:
                        result['errors'] = [str(e) for e in result['errors']]
                else:
                    return result
                return dict(auth=result)

        return dict(auth={'form': form.render()})

    @view_config(name='persona')
    def persona(self):
        request = self.request
        lm = request.layout_manager
        schema = schemas.PersonaSchema().bind(request=request)
        form = deform.Form(schema)
        form.action = request.view_name or 'persona'
        form.formid = 'persona'
        form.use_ajax = True
        form.ajax_options = self.ajax_options

        persona = dict(id=0 if self.request.user else -1)
        try:
            if request.method == 'POST':
                if request.view_name == 'persona':
                    persona = form.validate(request.POST.items())
                    if persona.get('id', None) == -1:
                        controller = horus.views.AuthController(request)
                        return controller.logout()
                    else:
                        # TODO: multiple personas
                        persona = None
            lm.layout.add_form('persona', form)
        except deform.exception.ValidationFailure as e:
            lm.layout.add_form('persona', e)
            return dict(persona={'form': e})

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
        lm = request.layout_manager
        result = {}

        for name in ['auth', 'persona']:
            subresult = getattr(self, name)()
            if isinstance(subresult, dict):
                result.update(subresult)

        result.update(
            css_links=lm.layout.css_links,
            js_links=lm.layout.js_links
        )

        return result


def includeme(config):
    config.scan(__name__)
