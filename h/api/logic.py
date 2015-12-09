# -*- coding: utf-8 -*-
import logging

from h import i18n

from h.api.models import Annotation
from h.api import search as search_lib


_ = i18n.TranslationString
log = logging.getLogger(__name__)


def create_annotation(fields):
    """Create and store an annotation."""
    annotation = Annotation(fields)
    search_lib.prepare(annotation)
    annotation.save()

    return annotation


def update_annotation(annotation, fields):
    """Update the given annotation with the given new fields."""
    annotation.update(fields)
    search_lib.prepare(annotation)
    annotation.save()


def delete_annotation(annotation):
    annotation.delete()
