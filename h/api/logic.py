# -*- coding: utf-8 -*-
import logging

from h import i18n

from h.api.models import Annotation
from h.api import search as search_lib


_ = i18n.TranslationString
log = logging.getLogger(__name__)


def create_annotation(fields, userid):
    """Create and store an annotation."""
    # Create Annotation instance
    annotation = Annotation(fields)
    annotation['user'] = userid

    # Save it in the database
    search_lib.prepare(annotation)
    annotation.save()

    log.debug('Created annotation; user: %s', annotation['user'])

    return annotation


def update_annotation(annotation, fields, userid):
    """Update the given annotation with the given new fields.

    :raises RuntimeError: if the fields attempt to change the annotation's
        permissions and has_admin_permission is False, or if they are
        attempting to move the annotation between groups.

    """
    # If the user is changing access permissions, check if it's allowed.
    permissions = annotation.get('permissions', {})
    changing_permissions = (
        'permissions' in fields and
        fields['permissions'] != permissions
    )
    if changing_permissions and userid not in permissions.get('admin', []):
        raise RuntimeError(
            _('Not authorized to change annotation permissions.'), 401)

    if 'group' in fields and 'group' in annotation:
        if fields['group'] != annotation.get('group'):
            raise RuntimeError(
                _("You can't move annotations between groups."), 401)

    # Update the annotation with the new data
    annotation.update(fields)

    # Save the annotation in the database, overwriting the old version.
    search_lib.prepare(annotation)
    annotation.save()


def delete_annotation(annotation):
    annotation.delete()
