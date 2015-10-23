# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import cgi
import urllib2
import urlparse

import jinja2
from dateutil import parser
from annotator import annotation
from annotator import document


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
    def title(self):
        """A title for this annotation."""
        document_ = self.get("document")
        if document_:
            return document_.get("title", "")
        else:
            return ""

    @property
    def filename(self):
        if self.uri and self.uri.startswith("file://"):
            return self.uri.split("/")[-1] or ""
        else:
            return ""

    @property
    def document_link(self):
        """Return a link to this annotation's document.

        Returns HTML strings like:

          <a href="{href}" title="{title}">{link_text}</a> ({domain})

        where:

        - {href} is the uri of the annotated document,
          if it has an http(s):// uri
        - {title} is the title of the document.
          If the document has no title then its uri will be used instead.
          If it's a local file:// uri then only the filename part is used,
          not the full path.
        - {link_text} is the same as {title}, but truncated with &hellip; if
          it's too long
        - {domain} is the domain name of the document's uri without
          the scheme (http(s)://) and www parts, e.g. "example.com".
          If it's a local file:// uri then the filename is used as the domain.
          If the domain is too long it is truncated with &hellip;.

        The ({domain}) part will be missing if it wouldn't be any different
        from the {link_text} part.

        The href="{href}" will be missing if there's no http(s) uri to link to
        for this annotation's document.

        User-supplied values are escaped so the string is safe for raw
        rendering (the returned string is actually a jinja2.Markup object and
        won't be escaped by Jinja2 when rendering).

        """
        uri = jinja2.escape(self.uri) or ""

        if uri.startswith("http://") or uri.startswith("https://"):
            href = uri
        else:
            href = ""

        if self.title:
            title = jinja2.escape(self.title)
            link_text = title
            if uri.startswith("file://"):
                domain = jinja2.escape(self.filename)
            else:
                domain = urlparse.urlparse(uri).hostname
        else:
            if uri.startswith("file://"):
                title = urllib2.unquote(jinja2.escape(self.filename))
                link_text = title
                domain = ""
            else:
                title = urllib2.unquote(uri)
                parts = urlparse.urlparse(uri)
                link_text = urllib2.unquote(parts.netloc + parts.path)
                domain = ""
        if domain == title:
            domain = ""

        def truncate(content, length=50):
            """Truncate the given string to at most length chars."""
            if len(content) <= length:
                return content
            else:
                return content[:length] + jinja2.Markup("&hellip;")

        if link_text:
            link_text = truncate(link_text)

        if domain:
            domain = truncate(domain)

        assert title, "The title should never be empty"
        assert link_text, "The link text should never be empty"
        if href and domain:
            link = ('<a href="{href}" title="{title}">{link_text}</a> '
                    '({domain})'.format(href=href, title=title,
                                        link_text=link_text, domain=domain))
        elif domain and not href:
            link = ('<a title="{title}">{link_text}</a> ({domain})'.format(
                title=title, link_text=link_text, domain=domain))
        elif href and not domain:
            link = '<a href="{href}" title="{title}">{link_text}</a>'.format(
                href=href, title=title, link_text=link_text)
        elif (not href) and (not domain):
            link = '<a title="{title}">{link_text}</a>'.format(
                title=title, link_text=link_text)
        else:
            assert False, "We should never get here"

        return jinja2.Markup(link)

    @property
    def uri(self):
        """This annotation's URI or an empty string."""
        return self.get("uri", "")

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
