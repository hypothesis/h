import colander
import deform
import pyramid_deform

from h import api


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
