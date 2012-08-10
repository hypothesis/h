from apex.models import AuthID, AuthUser
from colander import deferred, Invalid, Length, Schema, SchemaNode, String, Email
from deform.widget import (FormWidget, PasswordWidget, SelectWidget,
                           TextInputWidget)
from pyramid_deform import CSRFSchema

from . import api

# Deform validators
# =================

def login_validator(node, kw):
    """Validate a username and password."""
    valid = False
    if 'username' in kw:
        valid = AuthUser.check_password(
            login=kw['username'],
            password=kw['password']
        )
    if not valid:
        raise Invalid(
            node,
            "Your username or password is incorrect."
        )

def register_validator(node, kw):
    used = AuthUser.get_by_login(kw['username'])
    used = used or AuthUser.get_by_email(kw['email'])
    if used:
        raise Invalid(node, "That username or email is taken.")


# Form schemas
# ============

class LoginSchema(CSRFSchema):
    username = SchemaNode(
        String(),
        validator=Length(min=4, max=25),
        widget=TextInputWidget(
            autocapitalize="off",
            autocomplete="off",
            placeholder="Username or Email"
        )
    )
    password = SchemaNode(
        String(),
        widget=PasswordWidget(placeholder="Password"),
    )

class RegisterSchema(CSRFSchema):
    email = SchemaNode(
        String(),
        validator=Email(),
        widget=TextInputWidget(
            autocapitalize="off",
            autocomplete="off",
            placeholder="Email"
        )
    )
    username = SchemaNode(
        String(),
        validator=Length(min=4, max=25),
        widget=TextInputWidget(
            autocapitalize="off",
            autocomplete="off",
            placeholder="Username"
        )
    )
    password = SchemaNode(
        String(),
        validator=Length(min=6),
        widget=PasswordWidget(placeholder="Password"),
    )

class PersonaSchema(CSRFSchema):
    persona = SchemaNode(
        String(),
        widget=deferred(
            lambda node, kw: SelectWidget(
                values=(
                    api.users(kw['request']) +
                    [(-1, kw['request'].user and 'Sign out' or 'Not signed in')]
                )
            )
        ),
    )
