import codecs
import logging
from datetime import datetime, timedelta
from functools import cache

import colander
import deform
from sqlalchemy import select

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
from h.util.user import format_userid

_ = i18n.TranslationString
log = logging.getLogger(__name__)


@cache
def get_blacklist():
    # Try to load the blacklist file from disk. If, for whatever reason, we
    # can't load the file, then don't crash out, just log a warning about
    # the problem.
    try:
        with codecs.open("h/accounts/blacklist", encoding="utf-8") as handle:
            blacklist = handle.readlines()
    except (OSError, ValueError):  # pragma: no cover
        log.exception("unable to load blacklist")
        blacklist = []
    return set(line.strip().lower() for line in blacklist)  # noqa: C401


def unique_email(node, value):
    """Colander validator that ensures no user with this email exists."""
    request = node.bindings["request"]
    user = models.User.get_by_email(request.db, value, request.default_authority)
    if user and user.userid != request.authenticated_userid:
        msg = _("Sorry, an account with this email address already exists.")
        raise colander.Invalid(node, msg)


def unique_username(node, value):
    """Colander validator that ensures the username does not exist."""
    exc = colander.Invalid(node, _("This username is already taken."))
    request = node.bindings["request"]
    user = models.User.get_by_username(request.db, value, request.default_authority)
    if user:  # pragma: no cover
        raise exc

    # Don't allow recently-deleted usernames to be re-used.
    # This is to make sure that there's time for the user's data to be expunged
    # from all systems (for example: Elasticsearch) before we allow a new
    # account with the same username to be registered.
    # Otherwise new accounts could inherit dating belonging to deleted accounts.
    if request.db.scalars(
        select(models.UserDeletion.id)
        .where(
            models.UserDeletion.userid
            == format_userid(value, request.default_authority)
        )
        # 31 days is an arbitrary time delta that should be more than enough
        # time for all the previous user's data to be expunged.
        .where(models.UserDeletion.requested_at > datetime.now() - timedelta(days=31))  # noqa: DTZ005
    ).first():
        raise exc


def username_node():
    return colander.SchemaNode(
        colander.String(),
        validator=colander.All(
            validators.Length(min=USERNAME_MIN_LENGTH, max=USERNAME_MAX_LENGTH),
            colander.Regex(
                USERNAME_PATTERN,
                msg=_(
                    "Must have only letters, numbers, periods and underscores. May not start or end with period."
                ),
            ),
            unique_username,
            unblacklisted_username,
        ),
        title=_("Username"),
    )


def email_node(**kwargs):
    """Return a Colander schema node for a new user email."""
    return colander.SchemaNode(
        colander.String(),
        validator=colander.All(
            validators.Length(max=EMAIL_MAX_LENGTH), validators.Email(), unique_email
        ),
        **kwargs,
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
        **kwargs,
    )


def privacy_accepted_node():
    return colander.SchemaNode(
        colander.Boolean(),
        validator=privacy_acceptance_validator,
    )


def comms_opt_in_node():
    return colander.SchemaNode(
        colander.Boolean(),
        missing=None,
        default=False,
    )


class SignupSchema(CSRFSchema):
    username = username_node()
    email = email_node(title=_("Email address"))
    password = new_password_node(title=_("Password"))
    privacy_accepted = privacy_accepted_node()
    comms_opt_in = comms_opt_in_node()


class SocialLoginSignupSchema(colander.Schema):
    username = username_node()
    privacy_accepted = privacy_accepted_node()
    comms_opt_in = comms_opt_in_node()


class EmailAddSchema(colander.Schema):
    email = email_node()


class EmailChangeSchema(colander.Schema):
    email = email_node()
    password = password_node()

    def validator(self, node, value):
        exc = colander.Invalid(node)
        request = node.bindings["request"]
        svc = request.find_service(name="user_password")
        user = request.user

        if not svc.check_password(user, value.get("password")):
            exc["password"] = _("Wrong password.")

        if exc.children:
            raise exc


def new_password_confirm_node():
    """Return a 'Confirm new password' node.

    On forms for setting or changing a user's password this adds a 'Confirm new
    password' field to get the user to enter the new password a second time for
    confirmation.

    """
    # No validators: all validation is done on the schema's 'New password'
    # field and then it's up to the schema to validate that this node's value
    # matches the value of the 'New password' field.
    return colander.SchemaNode(
        colander.String(),
        title=_("Confirm new password"),
        widget=deform.widget.PasswordWidget(autocomplete="new-password"),
    )


class PasswordAddSchema(colander.Schema):
    new_password = new_password_node()
    new_password_confirm = new_password_confirm_node()

    def validator(self, node, value):
        exc = colander.Invalid(node)

        if value.get("new_password") != value.get("new_password_confirm"):
            exc["new_password_confirm"] = _("The passwords must match.")

        if exc.children:
            raise exc


class PasswordChangeSchema(colander.Schema):
    password = password_node()
    new_password = new_password_node()
    new_password_confirm = new_password_confirm_node()

    def validator(self, node, value):
        exc = colander.Invalid(node)
        request = node.bindings["request"]
        svc = request.find_service(name="user_password")
        user = request.user

        if value.get("new_password") != value.get("new_password_confirm"):
            exc["new_password_confirm"] = _("The passwords must match.")

        if not svc.check_password(user, value.get("password")):
            exc["password"] = _("Wrong password.")

        if exc.children:
            raise exc


class DeleteAccountSchema(CSRFSchema):
    password = password_node(title=_("Confirm password"))

    def validator(self, node, value):
        super().validator(node, value)

        request = node.bindings["request"]
        svc = request.find_service(name="user_password")

        if not svc.check_password(request.user, value.get("password")):
            exc = colander.Invalid(node)
            exc["password"] = _("Wrong password.")
            raise exc


class DeleteAccountSchemaNoPassword(CSRFSchema):
    username = colander.SchemaNode(
        colander.String(), title=_("Confirm your username to delete your account")
    )

    def validator(self, node, value):
        super().validator(node, value)

        request = node.bindings["request"]

        if value.get("username") != request.user.username:
            exc = colander.Invalid(node)
            exc["username"] = _("Wrong username.")
            raise exc


class NotificationsSchema(CSRFSchema):
    reply = colander.SchemaNode(colander.Boolean())
    mention = colander.SchemaNode(colander.Boolean())
    moderation = colander.SchemaNode(colander.Boolean())


def includeme(_config):  # pragma: no cover
    pass
