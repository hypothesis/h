import colander
import deform

from h import i18n, models
from h.schemas import validators
from h.schemas.base import CSRFSchema

_ = i18n.TranslationString


class ForgotPasswordSchema(CSRFSchema):
    email = colander.SchemaNode(
        colander.String(),
        validator=colander.All(validators.Email()),
        title=_("Email address"),
        widget=deform.widget.TextInputWidget(template="emailinput", autofocus=True),
    )

    def validator(self, node, value):
        super().validator(node, value)

        request = node.bindings["request"]
        email = value.get("email")
        user = models.User.get_by_email(request.db, email, request.default_authority)

        if user is None:
            err = colander.Invalid(node)
            err["email"] = _("Unknown email address.")
            raise err

        value["user"] = user
