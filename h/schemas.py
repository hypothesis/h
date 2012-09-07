import colander
import deform
import pyramid_deform

from h import api


class ControllerWidget(deform.widget.MappingWidget):
    def deserialize(self, field, pstruct):
        error = None
        result = {}

        if pstruct is colander.null:
            pstruct = {}

        formid = pstruct.get('__formid__', '')
        parts = formid.split('_')
        if len(parts) > 1:
            formid = parts[0]
            parts = parts[1:].join('_')
            pstruct['__formid__'] = parts
        else:
            parts = ''

        for num, subfield in enumerate(field.children):
            name = subfield.name
            subval = pstruct.get(name, colander.null)

            try:
                if name != formid:
                    result[name] = subfield.deserialize(colander.null)
                else:
                    result[name] = subfield.deserialize(subval)
            except colander.Invalid as e:
                result[name] = e.value
                if error is None:
                    error = colander.Invalid(field.schema, value=result)
                error.add(e, num)

        if error is not None:
            raise error

        return result

    def serialize(self, field, cstruct, readonly=False):
        if cstruct is (colander.null, None):
            cstruct = {}
        return

class Controller(colander.Mapping):
    widget_maker = ControllerWidget

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
