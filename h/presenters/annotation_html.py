# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from dateutil import parser

import jinja2

from h.presenters.document_html import DocumentHTMLPresenter


class AnnotationHTMLPresenter(object):
    """Wraps Annotation model objects and adds some HTML properties."""

    def __init__(self, annotation):
        self.annotation = annotation
        if self.annotation.document:
            self.document = DocumentHTMLPresenter(self.annotation.document)
        else:
            self.document = None

    def _get_selection(self):
        selectors = self.annotation.target_selectors
        for selector in selectors:
            if "exact" in selector:
                return selector["exact"]

    @property
    def uri(self):
        return jinja2.escape(self.annotation.target_uri)

    @property
    def text_rendered(self):
        """
        The body text of this annotation.

        This return value of this field is marked safe because it is rendered
        to HTML on write by :py:func:`h.util.markdown.render`, which must take
        care of all necessary escaping.
        """
        if self.annotation.text_rendered:
            return jinja2.Markup(self.annotation.text_rendered)
        return jinja2.Markup("")

    @property
    def quote(self):
        """The text in the document which this annotation refers to."""
        selection = self._get_selection()
        if selection:
            return jinja2.escape(selection)

        return ""

    @property
    def description(self):
        """An HTML-formatted description of this annotation.

        The description contains the target text that the user selected to
        annotate, as a <blockquote>, and the body text of the annotation
        itself.

        """

        description = ""

        selection = self._get_selection()
        if selection:
            selection = jinja2.escape(selection)
            description += "&lt;blockquote&gt;{selection}&lt;/blockquote&gt;".format(
                selection=selection
            )

        text = self.annotation.text
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
        created_string = jinja2.escape(self.annotation.created)
        return parser.parse(created_string).strftime("%Y-%m-%d")

    @property
    def document_link(self):
        """Return a link to this annotation's document."""
        if self.document:
            return self.document.link
        else:
            return ""

    @property
    def filename(self):
        """Return the filename of this annotation's document."""
        if self.document:
            return self.document.filename
        else:
            return ""

    @property
    def hostname_or_filename(self):
        """Return the hostname of this annotation's document."""
        if self.document:
            return self.document.hostname_or_filename
        else:
            return ""

    @property
    def href(self):
        """Return an href for this annotation's document, or ''."""
        if self.document:
            return self.document.href
        else:
            return ""

    @property
    def link_text(self):
        """Return some link text for this annotation's document."""
        if self.document:
            return self.document.link_text
        else:
            return ""

    @property
    def title(self):
        """Return a title for this annotation."""
        if self.document:
            return self.document.title
        else:
            return ""

    # Explicitly forward some annotation properties for convenient access.
    @property
    def id(self):
        return self.annotation.id

    @property
    def created(self):
        return self.annotation.created

    @property
    def updated(self):
        return self.annotation.updated

    @property
    def userid(self):
        return self.annotation.userid

    @property
    def username(self):
        return self.annotation.userid.split(":")[1].split("@")[0]

    @property
    def shared(self):
        return self.annotation.shared

    @property
    def tags(self):
        return self.annotation.tags
