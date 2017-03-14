# -*- coding: utf-8 -*-

"""
Code responsible for rendering domain objects into various output
formats.
"""

from __future__ import unicode_literals

from h.presenters.annotation_html import AnnotationHTMLPresenter
from h.presenters.document_html import DocumentHTMLPresenter

__all__ = (
    'AnnotationHTMLPresenter',
    'DocumentHTMLPresenter',
)
