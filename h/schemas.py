import colander
import deform
import pyramid_deform

from h import api
from horus import schemas


class SecurityCodeSchema(schemas.ResetPasswordSchema):
    security_code = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(256)
    )


class PersonaSchema(pyramid_deform.CSRFSchema):
    id = colander.SchemaNode(
        colander.Integer(),
        widget=colander.deferred(
            lambda node, kw: deform.widget.SelectWidget(
                values=(
                    api.personas(kw['request']) +
                    [(-1, 'Sign out' if kw['request'].user else 'Sign in')]
                )
            )
        ),
    )
