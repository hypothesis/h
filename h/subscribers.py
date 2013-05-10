from pyramid.events import subscriber, BeforeRender, NewRequest
from pyramid.renderers import get_renderer
from pyramid.settings import asbool

from h import events


@subscriber(BeforeRender)
def add_render_view_global(event):
    event['blocks'] = get_renderer('templates/blocks.pt').implementation()
    event['displayer'] = get_renderer('templates/displayer.pt').implementation()


@subscriber(NewRequest)
def csrf_token_header(event):
    request = event.request
    if request.method == 'POST':
        csrf_token = request.headers.get('X-XSRF-TOKEN')
        csrf_token = csrf_token or request.cookies.get('XSRF-TOKEN')
        if csrf_token:
            try:
                request.POST['csrf_token'] = csrf_token
            except KeyError:
                # Not a form content type
                request.GET['csrf_token'] = csrf_token


@subscriber(events.NewRegistrationEvent)
@subscriber(events.RegistrationActivatedEvent)
def registration(event):
    request = event.request
    settings = request.registry.settings
    autologin = asbool(settings.get('horus.autologin', False))

    if isinstance(event, events.RegistrationActivatedEvent) or autologin:
        request.user = event.user


def includeme(config):
    config.scan(__name__)
