# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import cgi
import urllib2
import urlparse

import jinja2
from dateutil import parser
from annotator import annotation
from annotator import document


def _format_document_link(href, title, link_text, hostname):
    """Return a document link for the given components.

    Helper function for the .document_link property below.

    The given href, title, link_text and hostname are assumed to be already
    safely escaped. The returned string will be a Markup object so that
    it can be rendered in Jinja2 templates without further escaped occurring.

    """
    if hostname and hostname in link_text:
        hostname = ""

    def truncate(content, length=50):
        """Truncate the given string to at most length chars."""
        if len(content) <= length:
            return content
        else:
            return content[:length] + jinja2.Markup("&hellip;")

    hostname = truncate(hostname)
    link_text = truncate(link_text)

    if href and hostname:
        link = '<a href="{href}" title="{title}">{link_text}</a> ({hostname})'
    elif hostname:
        link = '<a title="{title}">{link_text}</a> ({hostname})'
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



class Annotation(annotation.Annotation):
    __mapping__ = {
        'annotator_schema_version': {'type': 'string'},
        'created': {'type': 'date'},
        'updated': {'type': 'date'},
        'quote': {'type': 'string', 'analyzer': 'uni_normalizer'},
        'tags': {'type': 'string', 'analyzer': 'uni_normalizer'},
        'text': {'type': 'string', 'analyzer': 'uni_normalizer'},
        'deleted': {'type': 'boolean'},
        'uri': {
            'type': 'string',
            'index_analyzer': 'uri',
            'search_analyzer': 'uri',
            'fields': {
                'parts': {
                    'type': 'string',
                    'index_analyzer': 'uri_parts',
                    'search_analyzer': 'uri_parts',
                },
            },
        },
        'user': {'type': 'string', 'index': 'analyzed', 'analyzer': 'user'},
        'target': {
            'properties': {
                'source': {
                    'type': 'string',
                    'index_analyzer': 'uri',
                    'search_analyzer': 'uri',
                    'copy_to': ['uri'],
                },
                # We store the 'scope' unanalyzed and only do term filters
                # against this field.
                'scope': {
                    'type': 'string',
                    'index': 'not_analyzed',
                },
                'selector': {
                    'properties': {
                        'type': {'type': 'string', 'index': 'no'},

                        # Annotator XPath+offset selector
                        'startContainer': {'type': 'string', 'index': 'no'},
                        'startOffset': {'type': 'long', 'index': 'no'},
                        'endContainer': {'type': 'string', 'index': 'no'},
                        'endOffset': {'type': 'long', 'index': 'no'},

                        # Open Annotation TextQuoteSelector
                        'exact': {
                            'path': 'just_name',
                            'type': 'string',
                            'fields': {
                                'quote': {
                                    'type': 'string',
                                    'analyzer': 'uni_normalizer',
                                },
                            },
                        },
                        'prefix': {'type': 'string'},
                        'suffix': {'type': 'string'},

                        # Open Annotation (Data|Text)PositionSelector
                        'start': {'type': 'long'},
                        'end':   {'type': 'long'},
                    }
                }
            }
        },
        'permissions': {
            'index_name': 'permission',
            'properties': {
                'read': {'type': 'string'},
                'update': {'type': 'string'},
                'delete': {'type': 'string'},
                'admin': {'type': 'string'}
            }
        },
        'references': {'type': 'string'},
        'document': {
            'enabled': False,  # indexed explicitly by the save function
        },
        'thread': {
            'type': 'string',
            'analyzer': 'thread'
        },
        'group': {
            'type': 'string',
        }
    }
    __analysis__ = {
        'char_filter': {
            'strip_scheme': {
                'type': 'pattern_replace',
                'pattern': r'^(?:[A-Za-z][A-Za-z.+-]+:)?/{0,3}',
                'replacement': '',
            },
        },
        'filter': {
            'path_url': {
                'type': 'pattern_capture',
                'preserve_original': 'false',
                'patterns': [
                    r'([0-9.\-A-Za-z]+(?::\d+)?(?:/[^?#]*))?',
                ],
            },
            'rstrip_slash': {
                'type': 'pattern_replace',
                'pattern': '/$',
                'replacement': '',
            },
            'user': {
                'type': 'pattern_capture',
                'preserve_original': 'true',
                'patterns': ['^acct:((.+)@.*)$']
            }
        },
        'tokenizer': {
            'uri_part': {
                'type': 'pattern',
                'pattern': r'[#+/:=?.-]|(?:%2[3BF])|(?:%3[ADF])',
            }
        },
        'analyzer': {
            'thread': {
                'tokenizer': 'path_hierarchy'
            },
            'uri': {
                'tokenizer': 'keyword',
                'char_filter': ['strip_scheme'],
                'filter': ['path_url', 'rstrip_slash', 'lowercase'],
            },
            'uri_parts': {
                'tokenizer': 'uri_part',
                'filter': ['unique'],
            },
            'user': {
                'tokenizer': 'keyword',
                'filter': ['user', 'lowercase']
            },
            'uni_normalizer': {
                'tokenizer': 'icu_tokenizer',
                'filter': ['icu_folding']
            }
        }
    }

    @classmethod
    def get_analysis(cls):
        return cls.__analysis__

    @property
    def uri(self):
        """Return this annotation's URI or an empty string.

        The uri is escaped and safe to be rendered.

        The uri is a Markup object so it won't be double-escaped.

        """
        uri_ = self.get("uri")
        if uri_:

            # Convert non-string URIs into strings.
            # If the URI is already a unicode string this will do nothing.
            # We're assuming that URI cannot be a byte string.
            uri_ = unicode(uri_)

            return jinja2.escape(uri_)
        else:
            return ""

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
            # self.uri is already escaped so we don't need to escape it again
            # here.
            return self.uri.split("/")[-1]
        else:
            return ""

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
        document_ = self.get("document")
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
                title = unicode(title)

                return jinja2.escape(title)

        if self.filename:
            # self.filename is already escaped so we don't need to escape
            # it again here, but we do want to unquote it for readability.
            return urllib2.unquote(self.filename)
        else:
            # self.uri is already escaped so we don't need to escape
            # it again here, but we do want to unquote it for readability.
            return urllib2.unquote(self.uri)

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
            # self.filename is already escaped, doesn't need to be escaped
            # again here.
            return self.filename
        else:
            # self.uri is already escaped, doesn't need to be escaped again.
            hostname = urlparse.urlparse(self.uri).hostname

            # urlparse()'s .hostname is sometimes None.
            hostname = hostname or ""

            return hostname

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
        uri = self.uri  # self.uri is already escaped.
        if (uri.lower().startswith("http://") or
                uri.lower().startswith("https://")):
            return uri
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
        # self.title is already escaped.
        title = self.title

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
            targets = self.get("target")
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
            selection = cgi.escape(selection)
            description += u"&lt;blockquote&gt;{selection}&lt;/blockquote&gt;".format(
                selection=selection)

        text = self.get("text")
        if text:
            text = cgi.escape(text)
            description += u"{text}".format(text=text)

        return description

    @property
    def created_day_string(self):
        """A simple created day string for this annotation.

        Returns a day string like '2015-03-11' from the annotation's 'created'
        date.

        """
        return parser.parse(self["created"]).strftime("%Y-%m-%d")

    @property
    def parent(self):
        """
        Return the thread parent of this annotation, if it exists.
        """
        if 'references' not in self:
            return None
        if not isinstance(self['references'], list):
            return None
        if not self['references']:
            return None
        return Annotation.fetch(self['references'][-1])

    @property
    def target_links(self):
        """A list of the URLs to this annotation's targets."""
        links = []
        targets = self.get("target")
        if isinstance(targets, list):
            for target in targets:
                if not isinstance(target, dict):
                    continue
                source = target.get("source")
                if source is None:
                    continue
                links.append(source)
        return links


class Document(document.Document):
    __analysis__ = {}

    @classmethod
    def get_analysis(cls):
        return cls.__analysis__

    @classmethod
    def get_mapping(cls):
        mapping = super(Document, cls).get_mapping()
        mapping['document']['date_detection'] = False
        return mapping
