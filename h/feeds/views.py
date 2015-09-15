from pyramid.view import view_config
from pyramid import i18n

from h.api import search
from h import feeds


_ = i18n.TranslationStringFactory(__package__)


def _annotations(request):
    """Return the annotations from the search API."""
    results = search.search(request, request.params)
    return [search.render(a) for a in results['rows']]


@view_config(route_name='stream_atom')
def stream_atom(request):
    """An Atom feed of the /stream page."""
    return feeds.render_atom(
        request=request, annotations=_annotations(request),
        atom_url=request.route_url("stream_atom"),
        html_url=request.route_url("stream"),
        title=request.registry.settings.get("h.feed.title"),
        subtitle=request.registry.settings.get("h.feed.subtitle"))


@view_config(route_name='stream_rss')
def stream_rss(request):
    """An RSS feed of the /stream page."""
    return feeds.render_rss(
        request=request, annotations=_annotations(request),
        rss_url=request.route_url("stream_rss"),
        html_url=request.route_url("stream"),
        title=request.registry.settings.get("h.feed.title") or _(
            "Hypothesis Stream"),
        description=request.registry.settings.get("h.feed.description") or _(
            "The Web. Annotated"))


def includeme(config):
    config.add_route('stream_atom', '/stream.atom')
    config.add_route('stream_rss', '/stream.rss')
    config.scan(__name__)
