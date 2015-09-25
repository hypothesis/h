# -*- coding: utf-8 -*-

from h.api import models


def set_group_if_reply(annotation):
    """If the annotation is a reply set its group to that of its parent.

    If the annotation is a reply to another annotation (or a reply to a reply
    and so on) then it always belongs to the same group as the original
    annotation. If the client sent any 'group' field in the annotation we will
    just overwrite it!

    """
    def is_reply(annotation):
        """Return True if this annotation is a reply."""
        if annotation.get('references'):
            return True
        else:
            return False

    if not is_reply(annotation):
        return

    # Get the top-level annotation that this annotation is a reply
    # (or a reply-to-a-reply etc) to.
    top_level_annotation_id = annotation['references'][0]
    top_level_annotation = models.Annotation.fetch(top_level_annotation_id)

    # If we can't find the top-level annotation, there's nothing we can do, and
    # we should bail.
    if top_level_annotation is None:
        return

    if 'group' in top_level_annotation:
        annotation['group'] = top_level_annotation['group']
    else:
        if 'group' in annotation:
            del annotation['group']
