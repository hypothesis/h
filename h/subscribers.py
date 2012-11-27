from pyramid.events import subscriber, BeforeRender, NewRequest
from pyramid.renderers import get_renderer


@subscriber(BeforeRender)
def add_render_view_global(event):
    event['blocks'] = get_renderer('templates/blocks.pt').implementation()


@subscriber(NewRequest)
def csrf_token_header(event):
    request = event.request
    if request.method == 'POST':
        csrf_token = request.headers.get('X-XSRF-TOKEN')
        if csrf_token:
            try:
                request.POST['csrf_token'] = csrf_token
            except KeyError:
                # Not a form content type
                request.GET['csrf_token'] = csrf_token


def includeme(config):
    config.scan(__name__)
