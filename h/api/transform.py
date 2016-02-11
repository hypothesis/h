# -*- coding: utf-8 -*-

from h._compat import string_types
from h.api import nipsa
from h.api import uri


def set_group_if_reply(annotation, fetcher):
    """
    If the annotation is a reply set its group to that of its parent.

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
    top_level_annotation = fetcher(top_level_annotation_id)

    # If we can't find the top-level annotation, there's nothing we can do, and
    # we should bail.
    if top_level_annotation is None:
        return

    if 'group' in top_level_annotation:
        annotation['group'] = top_level_annotation['group']
    else:
        if 'group' in annotation:
            del annotation['group']


def insert_group_if_none(annotation):
    if not annotation.get('group'):
        annotation['group'] = '__world__'


def set_group_permissions(annotation):
    """Set the given annotation's permissions according to its group."""
    # If this annotation doesn't have a permissions field, we don't know how to
    # handle it and should bail.
    permissions = annotation.get('permissions')
    if permissions is None:
        return

    # For private annotations (visible only to the user who created them) the
    # client sends just the user's ID in the read permissions.
    is_private = (permissions.get('read') == [annotation['user']])

    if is_private:
        # The groups feature doesn't change the permissions for private
        # annotations at all.
        return

    group = annotation.get('group')
    if group == '__world__':
        # The groups feature doesn't change the permissions for annotations
        # that don't belong to a group.
        return

    group_principal = 'group:' + group

    # If the annotation belongs to a group, we make it so that only users who
    # are members of that group can read the annotation.
    annotation['permissions']['read'] = [group_principal]


def normalize_annotation_target_uris(annotation):
    if 'target' not in annotation:
        return
    if not isinstance(annotation['target'], list):
        return
    for target in annotation['target']:
        if not isinstance(target, dict):
            continue
        if 'source' not in target:
            continue
        if not isinstance(target['source'], string_types):
            continue
        target['scope'] = [uri.normalize(target['source'])]


def fix_old_style_comments(annotation):
    """
    Transform an old-style, targetless "comment" into one with a target.

    If this annotation has a URI, but no targets and no references, then it's
    an "old-style" comment or "page note". Detect this for old clients and
    rewrite the annotation target property.
    """
    def isempty(container, field):
        val = container.get(field)
        return val is None or val == []

    has_uri = annotation.get('uri') is not None
    has_no_targets = isempty(annotation, 'target')
    has_no_references = isempty(annotation, 'references')

    if has_uri and has_no_targets and has_no_references:
        annotation['target'] = [{'source': annotation.get('uri')}]


def add_nipsa(annotation):
    if 'user' in annotation and nipsa.has_nipsa(annotation['user']):
        annotation['nipsa'] = True
