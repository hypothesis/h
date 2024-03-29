from pyramid import i18n
from pyramid.view import view_config
from webob.multidict import MultiDict

from h.feeds import render_atom, render_rss
from h.search import Search
from h.services.annotation_read import AnnotationReadService

_ = i18n.TranslationStringFactory(__package__)


@view_config(route_name="stream_atom")
def stream_atom(request):
    """Get an Atom feed of the /stream page."""
    return render_atom(
        request=request,
        annotations=_annotations(request),
        atom_url=request.route_url("stream_atom"),
        html_url=request.route_url("stream"),
        title=request.registry.settings.get("h.feed.title"),
        subtitle=request.registry.settings.get("h.feed.subtitle"),
    )


@view_config(route_name="stream_rss")
def stream_rss(request):
    """Get an RSS feed of the /stream page."""
    return render_rss(
        request=request,
        annotations=_annotations(request),
        rss_url=request.route_url("stream_rss"),
        html_url=request.route_url("stream"),
        title=request.registry.settings.get("h.feed.title") or _("Hypothesis Stream"),
        description=request.registry.settings.get("h.feed.description")
        or _("The Web. Annotated"),
    )


def _annotations(request):
    """Return the annotations from the search API."""
    result = Search(request).run(MultiDict(request.params))

    return request.find_service(AnnotationReadService).get_annotations_by_id(
        ids=result.annotation_ids
    )
