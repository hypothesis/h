"""Functions for generating Atom feeds."""
import urlparse
import cgi
import datetime

from pyramid import i18n
from pyramid import renderers

from . import util

_ = i18n.TranslationStringFactory(__package__)


def _created_day_string_from_annotation(annotation):
    """Return a simple created day string for an annotation.

    Returns a day string like '2015-03-11' from a Hypothesis API "created"
    datetime string like '2015-03-11T10:43:54.537626+00:00'.

    """
    return datetime.datetime.strptime(
        annotation["created"][:10], "%Y-%m-%d").strftime("%Y-%m-%d")


def _atom_id_for_annotation(annotation, annotation_url):
    """Return an Atom entry ID for the given annotation.

    :param annotation: An annotation from the API
    :type annotation: dict

    :param annotation_url: A function that returns the HTML permalink for an
        annotation
    :type annotation_url: callable

    :returns: A tag URI (RFC 4151) for use as the ID for the Atom entry.
    :rtype: string

    """
    return u"tag:{domain},{day}:{id_}".format(
        domain=urlparse.urlparse(annotation_url(annotation)).netloc,
        day=_created_day_string_from_annotation(annotation),
        id_=annotation["id"])


def _feed_entry_from_annotation(
        annotation, annotation_url, annotation_api_url=None):
    """Return an Atom feed entry for the given annotation.

    :param annotation: An annotation from the API
    :type annotation: dict

    :param annotation_url: A function that returns the HTML permalink for an
        annotation
    :type annotation_url: callable

    :param annotation_api_url: A function that returns the JSON API link for an
        annotation
    :type annotation_api_url: callable

    :returns: A logical representation of the Atom feed entry as a dict,
        containing all of the data that a template would need to render the
        feed item to XML.
    :rtype: dict

    """
    parts = util.split_user(annotation["user"])
    if parts is None:
        name = annotation["user"]
    else:
        name = parts[0]
    document = annotation.get("document")
    if document:
        title = document.get("title", "")
    else:
        title = ""
    entry = {
        "id": _atom_id_for_annotation(annotation, annotation_url),
        "author": {"name": name},
        "title": title,
        "updated": annotation["updated"],
        "published": annotation["created"],
    }

    def get_selection(annotation):
        targets = annotation.get("target")
        if targets:
            for target in targets:
                for selector in target["selector"]:
                    if "exact" in selector:
                        return selector["exact"]

    content = ""

    selection = get_selection(annotation)
    if selection:
        selection = cgi.escape(selection)
        content += u"&lt;blockquote&gt;{selection}&lt;/blockquote&gt;".format(
            selection=selection)

    text = annotation.get("text")
    if text:
        text = cgi.escape(text)
        content += u"{text}".format(text=text)

    entry["content"] = content

    entry["links"] = []

    entry["links"].append({"rel": "alternate", "type": "text/html",
                           "href": annotation_url(annotation)})

    if annotation_api_url:
        entry["links"].append({"rel": "alternate", "type": "application/json",
                               "href": annotation_api_url(annotation)})

    return entry


def _feed_from_annotations(
        annotations, atom_url, annotation_url, annotation_api_url=None,
        html_url=None, title=None, subtitle=None):
    """Return an Atom feed for the given list of annotations.

    This returns a logical representation of an Atom feed as a Python dict
    containing all of the data that a template would need to render the feed
    to XML (including a list of dicts for the feed's entries).

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


def render_annotations(
        request, annotations, atom_url, html_url=None, title=None,
        subtitle=None):
    """Return an Atom feed of the given list of annotations.

    :param annotations: A list of annotations from the API
    :type annotations: list of dicts

    :param atom_url: The URL where this Atom feed will be hosted
        (the feed will contain a link to this URL)
    :type atom_url: unicode

    :param html_url: The URL to the HTML page that this Atom feed is a feed
        for (the feed will contain a link to this URL).
    :type html_url: unicode

    :param title: The title of the feed
    :type title: unicode

    :param subtitle: The subtitle of the feed
    :type subtitle: unicode

    :returns: An Atom feed as an XML string
    :rtype: unicode

    """
    def annotation_url(annotation):
        """Return the HTML permalink URL for the given annotation."""
        return request.resource_url(request.root, "a", annotation["id"])

    def annotation_api_url(annotation):
        """Return the JSON API URL for the given annotation."""
        return request.resource_url(request.root, "api", "annotations",
                                    annotation["id"])

    feed = _feed_from_annotations(
        annotations=annotations, atom_url=atom_url,
        annotation_url=annotation_url, annotation_api_url=annotation_api_url,
        html_url=html_url, title=title, subtitle=subtitle)

    return renderers.render(
        'h:templates/atom.xml', {"feed": feed}, request=request)
