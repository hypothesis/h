# -*- coding: utf-8 -*-
"""Functions for generating Atom feeds."""
from pyramid import i18n

from h import util
import h.feeds.util

_ = i18n.TranslationStringFactory(__package__)


def _feed_entry_from_annotation(
        annotation, annotation_url, annotation_api_url=None):
    """Return an Atom feed entry for the given annotation.

    :returns: A logical representation of the Atom feed entry as a dict,
        containing all of the data that a template would need to render the
        feed item to XML.
    :rtype: dict

    """
    try:
        name = util.split_user(annotation["user"])["username"]
    except ValueError:
        name = annotation["user"]
    entry = {
        "id": h.feeds.util.tag_uri_for_annotation(annotation, annotation_url),
        "author": {"name": name},
        "title": annotation.title,
        "updated": annotation["updated"],
        "published": annotation["created"],
        "content": annotation.description,
        "links": [
            {"rel": "alternate", "type": "text/html",
             "href": annotation_url(annotation)},
        ]
    }
    if annotation_api_url:
        entry["links"].append(
            {"rel": "alternate", "type": "application/json",
             "href": annotation_api_url(annotation)}
        )
    entry["links"].extend(
        [{"rel": "related", "href": link} for link in annotation.target_links])

    return entry


def feed_from_annotations(
        annotations, atom_url, annotation_url, annotation_api_url=None,
        html_url=None, title=None, subtitle=None):
    """Return an Atom feed for the given list of annotations.

    :returns: A logical representation of an Atom feed as a Python dict
        containing all of the data that a template would need to render the
        feed to XML (including a list of dicts for the feed's entries).
    :rtype: dict

    """
    links = [{"rel": "self", "type": "application/atom+xml", "href": atom_url}]

    if html_url:
        links.append(
            {"rel": "alternate", "type": "text/html", "href": html_url})

    entries = [
        _feed_entry_from_annotation(a, annotation_url, annotation_api_url)
        for a in annotations]

    feed = {
        "id": atom_url,
        "title": title or _("Hypothesis Stream"),
        "subtitle": subtitle or _("The Web. Annotated"),
        "entries": entries,
        "links": links
    }

    if annotations:
        feed["updated"] = annotations[0]["updated"]

    return feed
