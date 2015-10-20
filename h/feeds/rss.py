"""Functions for generating RSS feeds."""
from pyramid import i18n
from dateutil import parser

from h import util
import h.feeds.util


_ = i18n.TranslationStringFactory(__package__)


def _pubDate_string_from_annotation(annotation):
    """Return a correctly-formatted pubDate string for the given annotation.

    Return a pubDate string like 'Tue, 03 Jun 2003 09:39:21 GMT' from a
    Hypothesis API 'created' datetime string like
    '2015-03-11T10:43:54.537626+00:00'.

    Suitable for use as the contents of a <pubDate> element in an <item>
    element of an RSS feed.

    """
    return parser.parse(annotation['created']).strftime(
        '%a, %d %b %Y %H:%M:%S %z')


def _feed_item_from_annotation(annotation, annotation_url):
    """Return an RSS feed item for the given annotation.

    :returns: A logical representation of the RSS feed item as a dict,
        containing all of the data that a template would need to render the
        feed item to XML.
    :rtype: dict

    """
    try:
        name = util.split_user(annotation["user"])["username"]
    except ValueError:
        name = annotation["user"]
    return {
        "author": {"name": name},
        "title": annotation.title,
        "description": annotation.description,
        "pubDate": _pubDate_string_from_annotation(annotation),
        "guid": h.feeds.util.tag_uri_for_annotation(
            annotation, annotation_url),
        "link": annotation_url(annotation)
    }


def feed_from_annotations(annotations, annotation_url, rss_url, html_url,
                          title, description):
    """Return an RSS feed for the given list of annotations.

    :returns: A logical representation of an RSS feed as a Python dict
        containing all of the data that a template would need to render the
        feed to XML (including a list of dicts for the feed's items).
    :rtype: dict

    """
    feed = {
        'title': title,
        'rss_url': rss_url,
        'html_url': html_url,
        'description': description,
        # This is called entries not items so as not to clash with the dict's
        # standard .items() method.
        'entries': [
            _feed_item_from_annotation(annotation, annotation_url)
            for annotation in annotations]
    }

    if annotations:
        feed['pubDate'] = parser.parse(annotations[0]['updated']).strftime(
            '%a, %d %b %Y %H:%M:%S %Z')

    return feed
