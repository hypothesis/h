import colander
import deform

from h.schemas import validators

PASSWORD_MIN_LENGTH = 8


def new_password_node(**kwargs):
    """Return a Colander schema node for a new user password."""
    kwargs.setdefault("widget", deform.widget.PasswordWidget())
    return colander.SchemaNode(
        colander.String(),
        validator=validators.Length(min=PASSWORD_MIN_LENGTH),
        **kwargs
    )
