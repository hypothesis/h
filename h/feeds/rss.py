"""Functions for generating RSS feeds."""

from calendar import timegm
from email.utils import formatdate

from pyramid import i18n

from h import presenters
from h import util
import h.feeds.util


_ = i18n.TranslationStringFactory(__package__)


def _pubdate_string(timestamp):
    """Return a RFC2822-formatted pubDate string for the given timestamp.

    Return a pubDate string like 'Tue, 03 Jun 2003 09:39:21 -0000'.

    Suitable for use as the contents of a <pubDate> element in an <item>
    element of an RSS feed.

    """
    return formatdate(timegm(timestamp.utctimetuple()))


def _feed_item_from_annotation(annotation, annotation_url):
    """Return an RSS feed item for the given annotation.

    :returns: A logical representation of the RSS feed item as a dict,
        containing all of the data that a template would need to render the
        feed item to XML.
    :rtype: dict

    """
    try:
        name = util.user.split_user(annotation.userid)["username"]
    except ValueError:
        name = annotation.userid
    return {
        "author": {"name": name},
        "title": annotation.title,
        "description": annotation.description,
        "pubDate": _pubdate_string(annotation.created),
        "guid": h.feeds.util.tag_uri_for_annotation(annotation, annotation_url),
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
    annotations = [presenters.AnnotationHTMLPresenter(a) for a in annotations]

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
        feed['pubDate'] = _pubdate_string(annotations[0].updated)

    return feed
