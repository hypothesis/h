# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import colander
from deform.widget import (
    CheckboxWidget,
    SelectWidget,
    SequenceWidget,
    TextAreaWidget,
    TextInputWidget,
)

from h import i18n
from h.schemas import validators
from h.models.group import (
    GROUP_NAME_MIN_LENGTH,
    GROUP_NAME_MAX_LENGTH,
    GROUP_DESCRIPTION_MAX_LENGTH,
)
from h.schemas.base import CSRFSchema
from h.util import group_scope

_ = i18n.TranslationString

VALID_GROUP_TYPES = (("restricted", _("Restricted")), ("open", _("Open")))


@colander.deferred
def group_creator_validator(node, kw):
    def validate(form, value):
        """
        Validate that the creator username exists in the organization's authority.

        The creator of a group must belong to the same authority as the group
        and the group's organization.  Validate that there is a user matching
        the given creator username with the same authority as the chosen
        organization.

        """
        user_svc = kw["user_svc"]

        # A {pubid: models.Organization} dict of all the organizations
        # available to choose from in the form.
        organizations = kw["organizations"]

        # The pubid of the organization that the user has selected in the form.
        selected_pubid = value["organization"]

        # The models.Organization object for the selected organization.
        selected_organization = organizations[selected_pubid]

        # The authority that the new group will belong to if it is created.
        authority = selected_organization.authority

        # The username string that was entered for the group creator.
        creator_username = value["creator"]

        # The models.User object for the group creator user, or None.
        user = user_svc.fetch(creator_username, authority)

        if not user:
            # Either the username doesn't exist at all, or it has a different
            # authority than the chosen organization.
            exc = colander.Invalid(form, _("User not found"))
            exc["creator"] = _(
                "User {creator} not found at authority {authority}"
            ).format(creator=creator_username, authority=authority)
            raise exc

    return validate


def member_exists_validator(node, val):
    user_svc = node.bindings["request"].find_service(name="user")
    authority = node.bindings["request"].default_authority
    if user_svc.fetch(val, authority) is None:
        raise colander.Invalid(node, _("Username not found"))


def url_with_origin_validator(node, val):
    """Validate that entered URL can be parsed into a scope"""
    if not group_scope.parse_origin(val):
        raise colander.Invalid(
            node,
            _(
                "Each scope (prefix) must be a complete URL (e.g. 'http://www.example.com' or `https://foo.com/bar`)"
            ),
        )


@colander.deferred
def group_type_validator(node, kw):
    group = kw.get("group")
    if not group:
        return colander.OneOf([key for key, title in VALID_GROUP_TYPES])

    def validate(node, value):
        if group.type != value:
            raise colander.Invalid(
                node, _("Changing group type is currently not supported")
            )

    return validate


@colander.deferred
def group_organization_select_widget(node, kw):
    orgs = kw["organizations"]
    org_labels = []
    org_pubids = []
    for org in orgs.values():
        org_labels.append("{} ({})".format(org.name, org.authority))
        org_pubids.append(org.pubid)

    # `zip` returns an iterator in Python 3. The `SelectWidget` constructor
    # requires an actual list.
    return SelectWidget(values=list(zip(org_pubids, org_labels)))


class CreateAdminGroupSchema(CSRFSchema):
    def __init__(self, *args):
        super(CreateAdminGroupSchema, self).__init__(
            validator=group_creator_validator, *args
        )

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
        widget=SequenceWidget(add_subitem_text_template=_("Add scope"), min_len=1),
        validator=colander.Length(
            min=1, min_err=_("At least one scope must be specified")
        ),
    )

    members = colander.SequenceSchema(
        colander.Sequence(),
        colander.SchemaNode(
            colander.String(), name="member", validator=member_exists_validator
        ),
        title=_("Members"),
        hint=_("Add more members by their username to this group"),
        widget=SequenceWidget(add_subitem_text_template=_("Add member")),
        missing=None,
    )
