# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid.view import view_config
from pyramid import i18n

from memex import search
from memex import storage
from h import feeds


_ = i18n.TranslationStringFactory(__package__)


def _annotations(request):
    """Return the annotations from the search API."""
    result = search.Search(request).run(request.params)
    return storage.fetch_ordered_annotations(request.db, result.annotation_ids)


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
