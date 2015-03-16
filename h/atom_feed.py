import re
import urlparse
import cgi

import pyramid.i18n

_ = pyramid.i18n.TranslationStringFactory(__package__)


def _username_from_annotation(annotation):
    """Return the username from the given annotation.

    For example if the annotation contains
    {"user": "acct:seanh@hypothes.is", ...} then return "seanh".

    """
    match = re.match(r'^acct:([^@]+)@(.*)$', annotation["user"])
    username, domain = match.groups()
    return username


def _feed_entry_from_annotation(annotation):
    """Return an Atom feed entry for the given annotation.

    :param annotation: An augmented Hypothesis API annotation,
        as returned by augment_annotations().
    :type annotation: dict

    :returns: A logical representation of the Atom feed entry as a dict,
        containing all of the data that a template would need to render the
        feed item to XML.
    :rtype: dict

    """
    entry = {}
    entry["id"] = None  # FIXME
    entry["author"] = {"name": _username_from_annotation(annotation)}
    entry["title"] = annotation["document"]["title"]
    entry["updated"] = annotation["updated"]
    entry["published"] = annotation["created"]

    def get_selection(annotation):
        for target in annotation["target"]:
            for selector in target["selector"]:
                if "exact" in selector:
                    return selector["exact"]

    entry["content"] = (
        "&lt;blockquote&gt;{selection}&lt;/blockquote&gt;"
        "{text}".format(
            selection=cgi.escape(get_selection(annotation)),
            text=cgi.escape(annotation["text"])))

    entry["links"] = [
        {"rel": "alternate", "type": "text/html",
         "href": annotation["html_url"]},
        {"rel": "alternate", "type": "application/json",
         "href": annotation["json_url"]},
    ]

    return entry


def _feed_from_annotations(annotations, atom_url, html_url, title=None,
                           subtitle=None):
    """Return an Atom feed for the given list of annotations.

    This returns a logical representation of an Atom feed as a Python dict
    containing all of the data that a template would need to render the feed
    to XML (including a list of dicts for the feed's entries).

    """
    return {
        "id": None,  # FIXME
        "title": title or _("Hypothes.is Stream"),
        "subtitle": subtitle or _("The Web. Annotated"),
        "updated": annotations[0]["updated"],
        "entries": [_feed_entry_from_annotation(a) for a in annotations],
        "links": [
            {"rel": "self", "type": "application/atom", "href": atom_url},
            {"rel": "alternate", "type": "text/html", "href": html_url},
        ]
    }


def augment_annotations(request, annotations):
    """Augment a list of annotations with additional data from the request.

    Adds additional values which are needed to generate an Atom feed to the
    given list of annotations. These are values that we need the Pyramid
    request object to compute, we compute them here in a seperate function so
    that other functions in this module can be independent from Pyramid.

    """
    for annotation in annotations:
        annotation["html_url"] = request.resource_url(
            request.root, "a", annotation["id"])
        annotation["json_url"] = request.resource_url(
            request.root, "api", "annotation", annotation["id"])
    return annotations


def render_feed(request, annotations, atom_url, html_url,
                title=None, subtitle=None):
    """Return an Atom feed of the given list of annotations.

    :param annotations: An augmented list of Hypothes API annotation dicts,
        as returned by augment_annotations().

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
    return pyramid.renderers.render(
        'h:templates/atom.xml',
        {"feed": _feed_from_annotations(
            annotations, html_url, atom_url, title, subtitle)},
        request=request)
