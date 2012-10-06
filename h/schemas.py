import colander
import deform
import pyramid_deform

from h import api


class PersonaSchema(pyramid_deform.CSRFSchema):
    id = colander.SchemaNode(
        colander.Integer(),
        widget=colander.deferred(
            lambda node, kw: deform.widget.SelectWidget(
                values=api.personas(kw['request']),
                css_class='dropdown pull-right',
                template='tinyman'
            ),
        ),
        missing=-1
    )
