"""Utility functions for feed-generating code."""
from h._compat import urlparse

# See RFC4151 for details of the use and format of the tag date:
#
#   https://tools.ietf.org/html/rfc4151#section-2.1
FEED_TAG_DATE = '2015-09'


def tag_uri_for_annotation(annotation, annotation_url):
    """Return a tag URI (unique identifier) for the given annotation.

    Suitable for use as the value of the <id> element of an <entry> in an
    Atom feed, or the <guid> element of an <item> in an RSS feed.

    :returns: A tag URI (RFC 4151) for use as the ID for the Atom entry.
    :rtype: string

    """
    domain = urlparse.urlparse(annotation_url(annotation)).hostname
    return u"tag:{domain},{date}:{id_}".format(domain=domain,
                                               date=FEED_TAG_DATE,
                                               id_=annotation.id)
