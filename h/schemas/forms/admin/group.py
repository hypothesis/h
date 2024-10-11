import colander
from deform.widget import (
    CheckboxWidget,
    SelectWidget,
    SequenceWidget,
    TextAreaWidget,
    TextInputWidget,
)

from h import i18n
from h.models.group import (
    GROUP_DESCRIPTION_MAX_LENGTH,
    GROUP_NAME_MAX_LENGTH,
    GROUP_NAME_MIN_LENGTH,
)
from h.schemas import validators
from h.schemas.base import CSRFSchema
from h.util import group_scope

_ = i18n.TranslationString

VALID_GROUP_TYPES = (("restricted", _("Restricted")), ("open", _("Open")))


def username_validator(form, value):
    """
    Validate that the usernames exist in the organization's authority.

    The creator and members of a group must belong to the same authority as the
    group and the group's organization.
    """
    # Unlike other validators, this one is applied at the root level of the
    # form. This is because we need to read the value from the organization
    # to get the right authority to check the users. This isn't possible in
    # a specific validator, as it has no access to the global form data.

    user_svc = form.bindings["user_svc"]

    if group := form.bindings.get("group"):
        authority = group.authority
    elif organization := value.get("organization"):
        # If there's no group then fall back on the organization's authority
        # (this happens when creating a new group as opposed to editing an
        # existing one).
        authority = form.bindings.get("organizations")[organization].authority
    else:
        # If there's no group or organization then fall back on the default authority
        # (this happens when creating a new group and selecting no organization
        # for the group to belong to).
        authority = form.bindings["request"].default_authority

    exc = colander.Invalid(form, None)

    _validate_members(form, value["members"], authority, user_svc, exc)
    _validate_creator(value["creator"], authority, user_svc, exc)

    if exc.children:
        raise exc


def _validate_members(form, members_value, authority, user_svc, parent_exc):
    if not members_value:
        return

    members_node = form.get("members")
    member_node = members_node.get("member")
    members_error = colander.Invalid(members_node, None)

    for pos, node_value in enumerate(members_value):
        if not user_svc.fetch(node_value, authority):
            # If we don't attach errors in the right position, they don't
            # appear. For a list type value the correct position is the index
            # of the value in the list
            members_error.add(
                colander.Invalid(
                    member_node,
                    _("User '{username}' not found at authority '{authority}'").format(
                        username=node_value, authority=authority
                    ),
                ),
                pos=pos,
            )

    if members_error.children:
        # For non-lists the correct position is the index within the flat list
        # of children that colander stores internally for the parent node
        parent_exc.add(members_error, pos=form.children.index(members_node))


def _validate_creator(creator_username, authority, user_svc, parent_exc):
    if not user_svc.fetch(creator_username, authority):
        # Either the username doesn't exist at all, or it has a different
        # authority than the chosen organization.

        parent_exc["creator"] = _(
            "User '{username}' not found at authority '{authority}'"
        ).format(username=creator_username, authority=authority)


def url_with_origin_validator(node, val):
    """Validate that entered URL can be parsed into a scope."""
    if not group_scope.parse_origin(val):
        raise colander.Invalid(
            node,
            _(
                "Each scope (prefix) must be a complete URL (e.g. 'http://www.example.com' or `https://foo.com/bar`)"
            ),
        )


@colander.deferred
def group_type_validator(_node, kwargs):
    group = kwargs.get("group")
    if not group:
        return colander.OneOf([key for key, title in VALID_GROUP_TYPES])

    def validate(node, value):
        if group.type != value:
            raise colander.Invalid(
                node, _("Changing group type is currently not supported")
            )

    return validate


@colander.deferred
def group_organization_select_widget(_node, kwargs):
    orgs = kwargs["organizations"]
    org_labels = ["-- None --"]
    org_pubids = [""]
    for org in orgs.values():
        org_labels.append(f"{org.name} ({org.authority})")
        org_pubids.append(org.pubid)

    # `zip` returns an iterator. The `SelectWidget` constructor requires an
    # actual list.
    return SelectWidget(values=list(zip(org_pubids, org_labels)))


class AdminGroupSchema(CSRFSchema):
    def __init__(self, *args):
        super().__init__(validator=username_validator, *args)

    group_type = colander.SchemaNode(
        colander.String(),
        title=_("Group Type"),
        widget=SelectWidget(values=(("", _("Select")),) + VALID_GROUP_TYPES),
        validator=group_type_validator,
    )

    name = colander.SchemaNode(
        colander.String(),
        title=_("Group Name"),
        validator=validators.Length(
            min=GROUP_NAME_MIN_LENGTH, max=GROUP_NAME_MAX_LENGTH
        ),
        widget=TextInputWidget(max_length=GROUP_NAME_MAX_LENGTH),
    )

    organization = colander.SchemaNode(
        colander.String(),
        title=_("Organization"),
        description=_("Organization which this group belongs to"),
        widget=group_organization_select_widget,
        missing=None,
    )

    creator = colander.SchemaNode(
        colander.String(),
        title=_("Creator"),
        description=_("Username for this group's creator"),
        hint=_(
            'This user will be set as the "creator" of the group. Note that'
            " the user must be on the same authority as the group authority"
        ),
    )

    description = colander.SchemaNode(
        colander.String(),
        title=_("Description"),
        description=_("Optional group description"),
        validator=colander.Length(max=GROUP_DESCRIPTION_MAX_LENGTH),
        widget=TextAreaWidget(rows=3, max_length=GROUP_DESCRIPTION_MAX_LENGTH),
        missing=None,
    )

    # Although the default value of the enforce_scope property is True,
    # we need to allow the unchecking of the checkbox that represents it,
    # which means that empty values should be treated as False.
    enforce_scope = colander.SchemaNode(
        colander.Boolean(),
        hint=_(
            "Only allow annotations for documents within this group's defined scopes"
        ),
        widget=CheckboxWidget(css_class="form-checkbox--inline"),
        missing=False,
    )

    scopes = colander.SequenceSchema(
        colander.Sequence(),
        colander.SchemaNode(
            colander.String(), name="scope", validator=url_with_origin_validator
        ),
        title=_("Scopes"),
        hint=_(
            "Define where this group appears. A document's URL must start with one or more"
            " of the entered scope strings (e.g. 'http://www.example.com')"
        ),
        widget=SequenceWidget(add_subitem_text_template=_("Add scope")),
    )

    members = colander.SequenceSchema(
        colander.Sequence(),
        colander.SchemaNode(colander.String(), name="member"),
        title=_("Members"),
        hint=_("Add more members by their username to this group"),
        widget=SequenceWidget(add_subitem_text_template=_("Add member")),
        missing=None,
    )
