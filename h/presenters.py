"""A class that wraps Annotation model objects and adds some HTML properties."""
from __future__ import unicode_literals
import urlparse
import urllib2
from dateutil import parser

import jinja2

from h._compat import text_type


def _format_document_link(href, title, link_text, hostname):
    """Return a document link for the given components.

    Helper function for the .document_link property below.

    :returns: A document link as an HTML string, escaped and safe for
        rendering. The returned string is a Markup object so that it won't be
        double-escaped.

    """
    if hostname and hostname in link_text:
        hostname = ""

    def truncate(content, length=60):
        """Truncate the given string to at most length chars."""
        if len(content) <= length:
            return content
        else:
            return content[:length] + jinja2.Markup("&hellip;")

    hostname = truncate(hostname)
    link_text = truncate(link_text)

    if href and hostname:
        link = '<a href="{href}" title="{title}">{link_text}</a><br>({hostname})'
    elif hostname:
        link = '<a title="{title}">{link_text}</a><br>({hostname})'
    elif href:
        link = '<a href="{href}" title="{title}">{link_text}</a>'
    else:
        link = '<a title="{title}">{link_text}</a>'

    link = link.format(
        href=jinja2.escape(href),
        title=jinja2.escape(title),
        link_text=jinja2.escape(link_text),
        hostname=jinja2.escape(hostname))

    return jinja2.Markup(link)


class AnnotationHTMLPresenter(object):

    """Wraps Annotation model objects and adds some HTML properties."""

    def __init__(self, annotation):
        self.annotation = annotation

    def __getattr__(self, attr):
        return getattr(self.annotation, attr)

    def __getitem__(self, key):
        return self.annotation[key]

    @property
    def uri(self):
        return jinja2.escape(self.annotation.uri)

    @property
    def filename(self):
        """Return the filename of this annotation's document, or "".

        If the annotated URI is a file:// URI then return the filename part
        of it, otherwise return "".

        The filename is escaped and safe to be rendered.

        If it contains escaped characters then the filename will be a
        Markup object so it won't be double-escaped.

        """
        if self.uri.lower().startswith("file:///"):
            return jinja2.escape(self.uri.split("/")[-1])
        else:
            return ""

    @property
    def hostname_or_filename(self):
        """Return the hostname of this annotation's document.

        Returns the hostname part of the annotated document's URI, e.g.
        "www.example.com" for "http://www.example.com/example.html".

        If the URI is a file:// URI then return the filename part of it
        instead.

        The returned hostname or filename is escaped and safe to be rendered.

        If it contains escaped characters the returned value will be a Markup
        object so that it doesn't get double-escaped.

        """
        if self.filename:
            return jinja2.escape(self.filename)
        else:
            hostname = urlparse.urlparse(self.uri).hostname

            # urlparse()'s .hostname is sometimes None.
            hostname = hostname or ""

            return jinja2.escape(hostname)

    @property
    def title(self):
        """Return a title for this annotation.

        Return the annotated document's title or if the document has no title
        then return its filename (if it's a file:// URI) or its URI for
        non-file URIs.

        The title is escaped and safe to be rendered.

        If it contains escaped characters then the title will be a
        Markup object, so that it won't be double-escaped.

        """
        document_ = self.annotation.document
        if document_:
            try:
                title = document_["title"]
            except (KeyError, TypeError):
                # Sometimes document_ has no "title" key or isn't a dict at
                # all.
                title = ""
            if title:
                # Convert non-string titles into strings.
                # We're assuming that title cannot be a byte string.
                title = text_type(title)

                return jinja2.escape(title)

        if self.filename:
            return jinja2.escape(urllib2.unquote(self.filename))
        else:
            return jinja2.escape(urllib2.unquote(self.uri))

    @property
    def href(self):
        """Return an href for this annotation's document, or "".

        Returns a value suitable for use as the value of the href attribute in
        an <a> element in an HTML document.

        Returns an empty string if the annotation doesn't have a document with
        an http(s):// URI.

        The href is escaped and safe to be rendered.

        If it contains escaped characters the returned value will be a
        Markup object so that it doesn't get double-escaped.

        """
        uri = self.uri
        if (uri.lower().startswith("http://") or
                uri.lower().startswith("https://")):
            return jinja2.escape(uri)
        else:
            return ""

    @property
    def link_text(self):
        """Return some link text for this annotation's document.

        Return a text representation of this annotation's document suitable
        for use as the link text in a link like <a ...>{link_text}</a>.

        Returns the document's title if it has one, or failing that uses part
        of the annotated URI if the annotation has one.

        The link text is escaped and safe for rendering.

        If it contains escaped characters the returned value will be a
        Markup object so it doesn't get double-escaped.

        """
        title = jinja2.escape(self.title)

        # Sometimes self.title is the annotated document's URI (if the document
        # has no title). In those cases we want to remove the http(s):// from
        # the front and unquote it for link text.
        lower = title.lower()
        if lower.startswith("http://") or lower.startswith("https://"):
            parts = urlparse.urlparse(title)
            return urllib2.unquote(parts.netloc + parts.path)

        else:
            return title

    @property
    def document_link(self):
        """Return a link to this annotation's document.

        Returns HTML strings like:

          <a href="{href}" title="{title}">{link_text}</a> ({hostname})

        where:

        - {href} is the uri of the annotated document,
          if it has an http(s):// uri
        - {title} is the title of the document.
          If the document has no title then its uri will be used instead.
          If it's a local file:// uri then only the filename part is used,
          not the full path.
        - {link_text} is the same as {title}, but truncated with &hellip; if
          it's too long
        - {hostname} is the hostname name of the document's uri without
          the scheme (http(s)://) and www parts, e.g. "example.com".
          If it's a local file:// uri then the filename is used as the
          hostname.
          If the hostname is too long it is truncated with &hellip;.

        The ({hostname}) part will be missing if it wouldn't be any different
        from the {link_text} part.

        The href="{href}" will be missing if there's no http(s) uri to link to
        for this annotation's document.

        User-supplied values are escaped so the string is safe for raw
        rendering (the returned string is actually a Markup object and
        won't be escaped by Jinja2 when rendering).

        """
        return _format_document_link(
            self.href, self.title, self.link_text, self.hostname_or_filename)

    @property
    def description(self):
        """An HTML-formatted description of this annotation.

        The description contains the target text that the user selected to
        annotate, as a <blockquote>, and the body text of the annotation
        itself.

        """
        def get_selection():
            targets = self.annotation.get("target")
            if not isinstance(targets, list):
                return
            for target in targets:
                if not isinstance(target, dict):
                    continue
                selectors = target.get("selector")
                if not isinstance(selectors, list):
                    continue
                for selector in selectors:
                    if not isinstance(selector, dict):
                        continue
                    if "exact" in selector:
                        return selector["exact"]

        description = ""

        selection = get_selection()
        if selection:
            selection = jinja2.escape(selection)
            description += "&lt;blockquote&gt;{selection}&lt;/blockquote&gt;".format(
                selection=selection)

        text = self.annotation.get("text")
        if text:
            text = jinja2.escape(text)
            description += "{text}".format(text=text)

        return description

    @property
    def created_day_string(self):
        """A simple created day string for this annotation.

        Returns a day string like '2015-03-11' from the annotation's 'created'
        date.

        """
        created_string = jinja2.escape(self.annotation["created"])
        return parser.parse(created_string).strftime("%Y-%m-%d")
