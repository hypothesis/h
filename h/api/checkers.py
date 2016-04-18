"""jsonschema format checker functions."""
from pyramid import i18n

from h.api import exceptions


_ = i18n.TranslationStringFactory(__package__)


def check_group_permissions(effective_principals, group):
    """Check that the user has permission create an annotation in the group."""
    if group == '__world__':
        return True

    group_principal = 'group:{}'.format(group)
    if group_principal not in effective_principals:
        raise exceptions.ValidationError(
            'group: ' + _('You may not create annotations in groups you are '
                          'not a member of!'))

    return True
