# -*- coding: utf-8 -*-
"""Functions for generating Atom feeds."""
from __future__ import unicode_literals
from pyramid import i18n

from h import presenters
from h import util
import h.feeds.util

_ = i18n.TranslationStringFactory(__package__)


def _feed_entry_from_annotation(annotation, annotation_url, annotation_api_url=None):
    """Return an Atom feed entry for the given annotation.

    :returns: A logical representation of the Atom feed entry as a dict,
        containing all of the data that a template would need to render the
        feed item to XML.
    :rtype: dict

    """
    try:
        name = util.user.split_user(annotation.userid)["username"]
    except ValueError:
        name = annotation.userid

    entry = {
        "id": h.feeds.util.tag_uri_for_annotation(
            annotation.annotation, annotation_url
        ),
        "author": {"name": name},
        "title": annotation.title,
        "updated": _utc_iso8601_string(annotation.updated),
        "published": _utc_iso8601_string(annotation.created),
        "content": annotation.description,
        "links": [
            {
                "rel": "alternate",
                "type": "text/html",
                "href": annotation_url(annotation.annotation),
            }
        ],
    }
    if annotation_api_url:
        entry["links"].append(
            {
                "rel": "alternate",
                "type": "application/json",
                "href": annotation_api_url(annotation.annotation),
            }
        )

    return entry


def _utc_iso8601_string(timestamp):
    return timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")


def feed_from_annotations(
    annotations,
    atom_url,
    annotation_url,
    annotation_api_url=None,
    html_url=None,
    title=None,
    subtitle=None,
):
    """Return an Atom feed for the given list of annotations.

    :returns: A logical representation of an Atom feed as a Python dict
        containing all of the data that a template would need to render the
        feed to XML (including a list of dicts for the feed's entries).
    :rtype: dict

    """
    annotations = [presenters.AnnotationHTMLPresenter(a) for a in annotations]

    links = [{"rel": "self", "type": "application/atom+xml", "href": atom_url}]

    if html_url:
        links.append({"rel": "alternate", "type": "text/html", "href": html_url})

    entries = [
        _feed_entry_from_annotation(a, annotation_url, annotation_api_url)
        for a in annotations
    ]

    feed = {
        "id": atom_url,
        "title": title or _("Hypothesis Stream"),
        "subtitle": subtitle or _("The Web. Annotated"),
        "entries": entries,
        "links": links,
    }

    if annotations:
        feed["updated"] = _utc_iso8601_string(annotations[0].updated)

    return feed
