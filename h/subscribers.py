from pyramid.events import subscriber
from pyramid.events import BeforeRender
from pyramid.renderers import get_renderer


@subscriber(BeforeRender)
def add_render_view_global(event):
    event['main_template'] = get_renderer('templates/base.pt').implementation()
    event['blocks'] = get_renderer('templates/blocks.pt').implementation()


def includeme(config):
    config.scan(__name__)
