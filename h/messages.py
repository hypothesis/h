from pyramid.i18n import TranslationStringFactory
_ = TranslationStringFactory(__package__)


INVALID_FORM = _('There was a problem with your form submission.')
MISSING_PARAMETER = _('A required parameter is missing.')
NOT_LOGGED_IN = _('You must be logged in to do that!')
