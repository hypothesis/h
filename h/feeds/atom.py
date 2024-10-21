"""Functions for generating Atom feeds."""

from pyramid import i18n

import h.feeds.util
from h import presenters, util
from h.exceptions import InvalidUserId
from h.util.datetime import utc_iso8601

_ = i18n.TranslationStringFactory(__package__)


def _feed_entry_from_annotation(annotation, annotation_url, annotation_api_url=None):
    """
    Return an Atom feed entry for the given annotation.

    :returns: A logical representation of the Atom feed entry as a dict,
        containing all of the data that a template would need to render the
        feed item to XML.
    :rtype: dict

    """
    try:
        name = util.user.split_user(annotation.userid)["username"]
    except InvalidUserId:
        name = annotation.userid

    entry = {
        "id": h.feeds.util.tag_uri_for_annotation(
            annotation.annotation, annotation_url
        ),
        "author": {"name": name},
        "title": annotation.title,
        "updated": utc_iso8601(annotation.updated),
        "published": utc_iso8601(annotation.created),
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


def feed_from_annotations(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    annotations,
    atom_url,
    annotation_url,
    annotation_api_url=None,
    html_url=None,
    title=None,
    subtitle=None,
):
    """
    Return an Atom feed for the given list of annotations.

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
        feed["updated"] = utc_iso8601(annotations[0].updated)

    return feed
