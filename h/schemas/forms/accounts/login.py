import colander
import deform

from h import i18n
from h.schemas.base import CSRFSchema
from h.services.user import UserNotActivated

_ = i18n.TranslationString


@colander.deferred
def _deferred_username_widget(_node, kwargs):
    """Return a username widget that autofocuses if username isn't pre-filled."""
    return deform.widget.TextInputWidget(
        autofocus=_should_autofocus_username(kwargs), autocomplete="username"
    )


@colander.deferred
def _deferred_password_widget(_node, kwargs):
    """Return a password widget that autofocuses if username *is* pre-filled."""
    return deform.widget.PasswordWidget(
        autofocus=not _should_autofocus_username(kwargs),
        autocomplete="current-password",
    )


class LoginSchema(CSRFSchema):
    username = colander.SchemaNode(
        colander.String(),
        title=_("Username / email"),
        widget=_deferred_username_widget,
    )
    password = colander.SchemaNode(
        colander.String(), title=_("Password"), widget=_deferred_password_widget
    )

    def validator(self, node, value):
        super().validator(node, value)

        request = node.bindings["request"]
        username = value.get("username")
        password = value.get("password")

        user_service = request.find_service(name="user")
        user_password_service = request.find_service(name="user_password")

        try:
            user = user_service.fetch_for_login(username_or_email=username)
        except UserNotActivated as exc:
            err = colander.Invalid(node)
            err["username"] = _(
                "Please check your email and open the link to activate your account."
            )
            raise err from exc

        if user is None:
            err = colander.Invalid(node)
            err["username"] = _("User does not exist.")
            raise err

        if not user_password_service.check_password(user, password):
            err = colander.Invalid(node)
            err["password"] = _("Wrong password.")
            raise err

        value["user"] = user

    @staticmethod
    def default_values(request):
        """
        Return the default values to be pre-filled when the form is rendered.

        Returns a dict suitable for passing as the `appstruct` (default values)
        argument to LoginSchema.render().
        """
        return {
            # If there's a ?username=foobob query param then pre-fill the
            # username field with "foobob".
            "username": request.params.get("username", "")
        }


def _should_autofocus_username(kwargs):  # pragma: no cover
    """Return True if the username widget should be autofocused."""
    if LoginSchema.default_values(kwargs["request"]).get("username"):
        # The username widget is going to be pre-filled, so don't autofocus it.
        # (This allows the password widget, which the user still has to type
        # into, to be autofocused instead.)
        return False

    return True
