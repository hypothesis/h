# -*- coding: utf-8 -*-

"""
Code responsible for rendering domain objects into various output
formats.
"""

from __future__ import unicode_literals

from h.presenters.annotation_html import AnnotationHTMLPresenter
from h.presenters.annotation_json import AnnotationJSONPresenter
from h.presenters.annotation_jsonld import AnnotationJSONLDPresenter
from h.presenters.annotation_searchindex import AnnotationSearchIndexPresenter
from h.presenters.document_html import DocumentHTMLPresenter
from h.presenters.document_json import DocumentJSONPresenter
from h.presenters.document_searchindex import DocumentSearchIndexPresenter
from h.presenters.group_json import GroupJSONPresenter
from h.presenters.group_json import GroupsJSONPresenter
from h.presenters.user_json import UserJSONPresenter

__all__ = (
    "AnnotationHTMLPresenter",
    "AnnotationJSONPresenter",
    "AnnotationJSONLDPresenter",
    "AnnotationSearchIndexPresenter",
    "DocumentHTMLPresenter",
    "DocumentJSONPresenter",
    "DocumentSearchIndexPresenter",
    "GroupJSONPresenter",
    "GroupsJSONPresenter",
    "UserJSONPresenter",
)
