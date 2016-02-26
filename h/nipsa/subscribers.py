# -*- coding: utf-8 -*-

from h.nipsa import logic


def transform_annotation(event):
    """Add a {"nipsa": True} field on annotations whose users are flagged."""
    annotation = event.annotation
    if 'user' in annotation and logic.has_nipsa(annotation['user']):
        annotation['nipsa'] = True
