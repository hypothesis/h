import codecs
import logging
from functools import lru_cache

import colander
import deform
from jinja2 import Markup

from h import i18n, models
from h.models.user import (
    EMAIL_MAX_LENGTH,
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
    USERNAME_PATTERN,
)
from h.schemas import validators
from h.schemas.base import CSRFSchema
from h.schemas.forms.accounts.util import PASSWORD_MIN_LENGTH

_ = i18n.TranslationString
log = logging.getLogger(__name__)


@lru_cache(maxsize=None)
def get_blacklist():
    # Try to load the blacklist file from disk. If, for whatever reason, we
    # can't load the file, then don't crash out, just log a warning about
    # the problem.
    try:  # pylint: disable=too-many-try-statements
        with codecs.open("h/accounts/blacklist", encoding="utf-8") as handle:
            blacklist = handle.readlines()
    except (IOError, ValueError):  # pragma: no cover
        log.exception("unable to load blacklist")
        blacklist = []
    return set(line.strip().lower() for line in blacklist)


def unique_email(node, value):
    """Colander validator that ensures no user with this email exists."""
    request = node.bindings["request"]
    user = models.User.get_by_email(request.db, value, request.default_authority)
    if user and user.userid != request.authenticated_userid:
        msg = _("Sorry, an account with this email address already exists.")
        raise colander.Invalid(node, msg)


def unique_username(node, value):
    """Colander validator that ensures the username does not exist."""
    request = node.bindings["request"]
    user = models.User.get_by_username(request.db, value, request.default_authority)
    if user:  # pragma: no cover
        msg = _("This username is already taken.")
        raise colander.Invalid(node, msg)


def email_node(**kwargs):
    """Return a Colander schema node for a new user email."""
    return colander.SchemaNode(
        colander.String(),
        validator=colander.All(
            validators.Length(max=EMAIL_MAX_LENGTH), validators.Email(), unique_email
        ),
        widget=deform.widget.TextInputWidget(
            template="emailinput", autocomplete="username"
        ),
        **kwargs
    )


def unblacklisted_username(node, value, blacklist=None):
    """Colander validator that ensures the username is not blacklisted."""
    if blacklist is None:
        blacklist = get_blacklist()
    if value.lower() in blacklist:
        # We raise a generic "user with this name already exists" error so as
        # not to make explicit the presence of a blacklist.
        msg = _(
            "Sorry, an account with this username already exists. "
            "Please enter another one."
        )
        raise colander.Invalid(node, msg)


def privacy_acceptance_validator(node, value):
    """Add colander validator that ensures privacy acceptance checkbox checked."""
    if not value:
        msg = _("Acceptance of the privacy policy is required")
        raise colander.Invalid(node, msg)


def password_node(**kwargs):
    """Return a Colander schema node for an existing user password."""
    kwargs.setdefault(
        "widget", deform.widget.PasswordWidget(autocomplete="current-password")
    )
    return colander.SchemaNode(colander.String(), **kwargs)


def new_password_node(**kwargs):
    """Return a Colander schema node for a new user password."""
    kwargs.setdefault(
        "widget", deform.widget.PasswordWidget(autocomplete="new-password")
    )
    return colander.SchemaNode(
        colander.String(),
        validator=validators.Length(min=PASSWORD_MIN_LENGTH),
        **kwargs
    )


def _privacy_accepted_message():
    terms_links = {
        # pylint:disable=consider-using-f-string
        "privacy_policy": '<a class="link" href="{href}">{text}</a>'.format(
            href="https://web.hypothes.is/privacy/", text=_("privacy policy")
        ),
        "terms_of_service": '<a class="link" href="{href}">{text}</a>'.format(
            href="https://web.hypothes.is/terms-of-service/", text=_("terms of service")
        ),
        "community_guidelines": '<a class="link" href="{href}">{text}</a>'.format(
            href="https://web.hypothes.is/community-guidelines/",
            text=_("community guidelines"),
        ),
    }

    privacy_msg = _(
        "I have read and agree to the {privacy}, {tos}, and {community}."
    ).format(
        privacy=terms_links["privacy_policy"],
        tos=terms_links["terms_of_service"],
        community=terms_links["community_guidelines"],
    )

    return privacy_msg


class RegisterSchema(CSRFSchema):
    username = colander.SchemaNode(
        colander.String(),
        validator=colander.All(
            validators.Length(min=USERNAME_MIN_LENGTH, max=USERNAME_MAX_LENGTH),
            colander.Regex(
                USERNAME_PATTERN,
                msg=_("Must have only letters, numbers, periods, and underscores."),
            ),
            unique_username,
            unblacklisted_username,
        ),
        title=_("Username"),
        hint=_(
            "Must be between {min} and {max} characters, containing only "
            "letters, numbers, periods, and underscores."
        ).format(min=USERNAME_MIN_LENGTH, max=USERNAME_MAX_LENGTH),
        widget=deform.widget.TextInputWidget(autofocus=True),
    )
    email = email_node(title=_("Email address"))
    password = new_password_node(title=_("Password"))

    privacy_accepted = colander.SchemaNode(
        colander.Boolean(),
        description=Markup(_privacy_accepted_message()),
        validator=privacy_acceptance_validator,
        widget=deform.widget.CheckboxWidget(
            omit_label=True, css_class="form-checkbox--inline"
        ),
    )

    comms_opt_in = colander.SchemaNode(
        colander.Boolean(),
        description=_("I would like to receive news about annotation and Hypothesis."),
        widget=deform.widget.CheckboxWidget(
            omit_label=True, css_class="form-checkbox--inline"
        ),
        missing=None,
        default=False,
    )


class EmailChangeSchema(CSRFSchema):
    email = email_node(title=_("Email address"))
    # No validators: all validation is done on the email field
    password = password_node(title=_("Confirm password"), hide_until_form_active=True)

    def validator(self, node, value):
        super().validator(node, value)
        exc = colander.Invalid(node)
        request = node.bindings["request"]
        svc = request.find_service(name="user_password")
        user = request.user

        if not svc.check_password(user, value.get("password")):
            exc["password"] = _("Wrong password.")

        if exc.children:
            raise exc


class PasswordChangeSchema(CSRFSchema):
    password = password_node(title=_("Current password"), inactive_label=_("Password"))
    new_password = new_password_node(
        title=_("New password"), hide_until_form_active=True
    )
    # No validators: all validation is done on the new_password field and we
    # merely assert that the confirmation field is the same.
    new_password_confirm = colander.SchemaNode(
        colander.String(),
        title=_("Confirm new password"),
        widget=deform.widget.PasswordWidget(autocomplete="new-password"),
        hide_until_form_active=True,
    )

    def validator(self, node, value):  # pragma: no cover
        super().validator(node, value)
        exc = colander.Invalid(node)
        request = node.bindings["request"]
        svc = request.find_service(name="user_password")
        user = request.user

        if value.get("new_password") != value.get("new_password_confirm"):
            exc["new_password_confirm"] = _("The passwords must match")

        if not svc.check_password(user, value.get("password")):
            exc["password"] = _("Wrong password.")

        if exc.children:
            raise exc


class NotificationsSchema(CSRFSchema):
    types = (("reply", _("Email me when someone replies to one of my annotations.")),)

    notifications = colander.SchemaNode(
        colander.Set(),
        widget=deform.widget.CheckboxChoiceWidget(omit_label=True, values=types),
    )


def includeme(_config):  # pragma: no cover
    pass
