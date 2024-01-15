from urllib.parse import unquote, urlparse

import markupsafe


class DocumentHTMLPresenter:
    """Wraps Document model objects and adds some HTML properties."""

    def __init__(self, document):
        self.document = document

    @property
    def filename(self):
        """
        Return the filename of this document, or ''.

        If the document's URI is a file:// URI then return the filename part
        of it, otherwise return ''.

        The filename is escaped and safe to be rendered.

        If it contains escaped characters then the filename will be a
        Markup object so it won't be double-escaped.

        """
        if self.uri.lower().startswith("file:///"):
            return markupsafe.escape(self.uri.split("/")[-1])
        return ""

    @property
    def href(self):
        """
        Return an href for this document, or ''.

        Returns a value suitable for use as the value of the href attribute in
        an <a> element in an HTML document.

        Returns an empty string if the document doesn't have an http(s):// URI.

        The href is escaped and safe to be rendered.

        If it contains escaped characters the returned value will be a
        Markup object so that it doesn't get double-escaped.

        """
        if self.document.web_uri:
            return markupsafe.escape(self.document.web_uri)
        return ""

    @property
    def hostname_or_filename(self):
        """
        Return the hostname or filename of this document.

        Returns the hostname part of the document's URI, e.g.
        'www.example.com' for 'http://www.example.com/example.html'.

        If the URI is a file:// URI then return the filename part of it
        instead.

        The returned hostname or filename is escaped and safe to be rendered.

        If it contains escaped characters the returned value will be a Markup
        object so that it doesn't get double-escaped.
        """
        if self.filename:
            return markupsafe.escape(unquote(self.filename))

        hostname = urlparse(self.uri).hostname

        # urlparse()'s .hostname is sometimes None.
        hostname = hostname or ""

        return markupsafe.escape(hostname)

    @property
    def link(self):
        """
        Return a link to this document.

        Returns HTML strings like:
          <a href="{href}" title="{title}">{link_text}</a> {hostname}

          <em>Local file:</em> {title}<br>{hostname}

        where:

        - {href} is the uri of the document, if it has an http(s):// uri
        - {title} is the title of the document.
          If the document has no title then its uri will be used instead.
          If it's a local file:// uri then only the filename part is used,
          not the full path.
        - {link_text} is the same as {title}, but truncated with &hellip; if
          it's too long
        - {hostname} is the hostname name of the document's uri without
          the scheme (http(s)://) and www parts, e.g. 'example.com'.
          If it's a local file:// uri then the filename is used as the
          hostname.
          If the hostname is too long it is truncated with &hellip;.

        The {hostname} part will be missing if it wouldn't be any different
        from the {link_text} part.

        The href="{href}" will be missing if there's no http(s) uri to link to
        for this annotation's document.

        User-supplied values are escaped so the string is safe for raw
        rendering (the returned string is actually a Markup object and
        won't be escaped by Jinja2 when rendering).
        """
        return _format_document_link(
            self.href, self.title, self.link_text, self.hostname_or_filename
        )

    @property
    def link_text(self):
        """
        Return some link text for this document.

        Return a text representation of this document suitable for use as the
        link text in a link like <a ...>{link_text}</a>.

        Returns the document's title if it has one, or failing that uses part
        of the document's URI if it has one.

        The link text is escaped and safe for rendering.

        If it contains escaped characters the returned value will be a
        Markup object so it doesn't get double-escaped.

        """
        title = markupsafe.escape(self.title)

        # Sometimes self.title is the annotated document's URI (if the document
        # has no title). In those cases we want to remove the http(s):// from
        # the front and unquote it for link text.
        lower = title.lower()
        if lower.startswith("http://") or lower.startswith("https://"):
            parts = urlparse(title)
            return unquote(parts.netloc + parts.path)

        return title

    @property
    def title(self):
        """
        Return a title for this document.

        Return the document's title or if the document has no title then return
        its filename (if it's a file:// URI) or its URI for non-file URIs.

        The title is escaped and safe to be rendered.

        If it contains escaped characters then the title will be a
        Markup object, so that it won't be double-escaped.

        """
        title = self.document.title
        if title:
            # Convert non-string titles into strings.
            # We're assuming that title cannot be a byte string.
            title = str(title)
            return markupsafe.escape(title)

        if self.filename:
            return markupsafe.escape(unquote(self.filename))

        return markupsafe.escape(unquote(self.uri))

    @property
    def uri(self):
        if self.document.document_uris:
            return markupsafe.escape(self.document.document_uris[0].uri)
        return ""

    @property
    def web_uri(self):
        via_prefix = "https://via.hypothes.is/"
        web_uri = self.document.web_uri

        if web_uri and web_uri != via_prefix and web_uri.startswith(via_prefix):
            web_uri = web_uri[len(via_prefix) :]

        return web_uri


def _format_document_link(href, title, link_text, host_or_filename):  # pragma: no cover
    """
    Return a document link for the given components.

    Helper function for the .document_link property below.

    :returns: A document link as an HTML string, escaped and safe for
        rendering. The returned string is a Markup object so that it won't be
        double-escaped.

    """
    if href and host_or_filename and host_or_filename in link_text:
        host_or_filename = ""
    elif not href and title == host_or_filename:
        title = ""

    def truncate(content, length=55):
        """Truncate the given string to at most length chars."""
        if len(content) <= length:
            return content

        return content[:length] + markupsafe.Markup("&hellip;")

    host_or_filename = truncate(host_or_filename)
    link_text = truncate(link_text)

    if href and host_or_filename:
        link = '<a href="{href}" title="{title}">{link_text}</a><br>{host_or_filename}'
    elif href:
        link = '<a href="{href}" title="{title}">{link_text}</a>'
    else:
        link = "<em>Local file:</em> {title}"
        if host_or_filename:
            link += "<br>{host_or_filename}"

    link = link.format(
        href=markupsafe.escape(href),
        title=markupsafe.escape(title),
        link_text=markupsafe.escape(link_text),
        host_or_filename=markupsafe.escape(host_or_filename),
    )

    return markupsafe.Markup(link)
