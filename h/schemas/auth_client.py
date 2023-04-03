import colander
import deform

from h import i18n
from h.models.auth_client import GrantType
from h.schemas.base import CSRFSchema, enum_type

_ = i18n.TranslationString
GrantTypeSchemaType = enum_type(GrantType)


class CreateAuthClientSchema(CSRFSchema):
    name = colander.SchemaNode(
        colander.String(),
        title=_("Name"),
        hint=_("This will be displayed to users in the authorization prompt"),
    )

    authority = colander.SchemaNode(
        colander.String(),
        title=_("Authority"),
        hint=_("Set of users whose data this client can interact with"),
    )

    grant_type = colander.SchemaNode(
        GrantTypeSchemaType(),
        missing=None,
        title=_("Grant type"),
        hint=_(
            '"authorization_code" for most applications, '
            '"jwt_bearer" for keys for JWT grants used by publishers, '
            '"client_credentials" for allowing access to the user creation API'
        ),
    )

    trusted = colander.SchemaNode(
        colander.Boolean(),
        missing=False,
        widget=deform.widget.CheckboxWidget(
            omit_label=False, css_class="form-checkbox--inline"
        ),
        title=_("Trusted ⚠️"),
        hint=_(
            "Trusted clients do not require user approval. "
            "⚠️ Only enable this for official Hypothesis clients."
        ),
    )

    redirect_url = colander.SchemaNode(
        colander.String(),
        missing=None,
        title=_("Redirect URL"),
        hint=_(
            "The browser will redirect to this URL after "
            'authorization. Required if grant type is "authorization_code"'
        ),
    )

    def validator(self, node, value):
        super().validator(node, value)

        grant_type = value.get("grant_type")
        redirect_url = value.get("redirect_url")

        # There is currently a DB constraint that authorization_code clients
        # must have a redirect URL. For browser extensions this can create a
        # chicken-and-egg problem because the extension must be published to
        # allocate an extension ID, which then appears in the redirect URL. The
        # workaround in this case is to use a temporary URL and update it later.
        if grant_type == GrantType.authorization_code and not redirect_url:
            err = colander.Invalid(node)
            err["redirect_url"] = _('Required when grant type is "authorization_code"')
            raise err


class EditAuthClientSchema(CreateAuthClientSchema):
    # Read-only fields, listed in the form so that the user can easily copy and
    # paste them into their client's configuration.

    client_id = colander.SchemaNode(colander.String(), title=_("Client ID"))

    client_secret = colander.SchemaNode(
        colander.String(),
        missing=None,
        title=_("Client secret"),
        hint=_(
            "Secret used to authenticate confidential clients "
            "(ie. those which do not perform token exchange "
            "directly in the browser)"
        ),
    )
