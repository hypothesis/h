import colander
import deform
import slugify

from h import i18n
from h.accounts.schemas import CSRFSchema
from h.models.group import (
    GROUP_DESCRIPTION_MAX_LENGTH,
    GROUP_NAME_MAX_LENGTH,
    GROUP_NAME_MIN_LENGTH,
)
from h.schemas import validators

_ = i18n.TranslationString


def unblacklisted_group_name_slug(node, value):
    """Colander validator that ensures the "slugified" group name is not blacklisted."""
    if slugify.slugify(value).lower() in {"edit", "leave"}:
        raise colander.Invalid(
            node,
            _("Sorry, this group name is not allowed. " "Please choose another one."),
        )


def group_schema(autofocus_name=False):
    """Return a schema for the form for creating or editing a group."""

    schema = CSRFSchema()
    name = colander.SchemaNode(
        colander.String(),
        name="name",
        title=_("Name"),
        validator=colander.All(
            validators.Length(min=GROUP_NAME_MIN_LENGTH, max=GROUP_NAME_MAX_LENGTH),
            unblacklisted_group_name_slug,
        ),
        widget=deform.widget.TextInputWidget(
            autofocus=autofocus_name,
            show_required=True,
            css_class="group-form__name-input js-group-name-input",
            disable_autocomplete=True,
            label_css_class="group-form__name-label",
            max_length=GROUP_NAME_MAX_LENGTH,
        ),
    )

    description = colander.SchemaNode(
        colander.String(),
        name="description",
        title=_("Description"),
        validator=validators.Length(max=GROUP_DESCRIPTION_MAX_LENGTH),
        missing=None,
        widget=deform.widget.TextAreaWidget(
            css_class="group-form__description-input",
            label_css_class="group-form__description-label",
            min_length=0,
            max_length=GROUP_DESCRIPTION_MAX_LENGTH,
        ),
    )

    schema.add(name)
    schema.add(description)

    return schema
