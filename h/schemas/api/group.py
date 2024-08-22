"""Schema for validating API group resources."""

from h.i18n import TranslationString as _
from h.models.group import (
    GROUP_DESCRIPTION_MAX_LENGTH,
    GROUP_NAME_MAX_LENGTH,
    GROUP_NAME_MIN_LENGTH,
)
from h.schemas.base import JSONSchema, ValidationError
from h.util.group import GROUPID_PATTERN, split_groupid

GROUP_SCHEMA_PROPERTIES = {
    "name": {
        "type": "string",
        "minLength": GROUP_NAME_MIN_LENGTH,
        "maxLength": GROUP_NAME_MAX_LENGTH,
    },
    "description": {"type": "string", "maxLength": GROUP_DESCRIPTION_MAX_LENGTH},
    "groupid": {"type": "string", "pattern": GROUPID_PATTERN},
    "type": {"enum": ["private", "restricted", "open"]},
}


class GroupAPISchema(JSONSchema):
    """Base class for validating group resource API data."""

    schema = {"type": "object", "properties": GROUP_SCHEMA_PROPERTIES}

    def __init__(self, group_authority=None, default_authority=None):
        """
        Initialize a new group schema instance.

        The ``group_authority`` and ``default_authority`` args are used for
        validating any ``groupid`` present in the data being validated.

        :arg group_authority: The authority associated with the group resource.
                              (default None)
        :arg default_authority: The service's default authority (default None)

        """
        super().__init__()
        self.group_authority = group_authority
        self.default_authority = default_authority

    def validate(self, data):
        """
        Validate against the JSON schema and also valid any ``groupid`` present.

        :raise h.schemas.ValidationError: if any part of validation fails
        :return: The validated data
        :rtype: dict

        """

        appstruct = super().validate(data)
        appstruct = self._whitelisted_fields_only(appstruct)
        self._validate_name(appstruct)
        self._validate_groupid(appstruct)

        return appstruct

    def _validate_name(self, appstruct):
        name = appstruct.get("name")

        if name and name.strip() != name:
            raise ValidationError(
                "Group names can't have leading or trailing whitespace."
            )

    def _validate_groupid(self, appstruct):
        """
        Validate the ``groupid`` to make sure it adheres to authority restrictions.

        ``groupid`` is only allowed if the authority of the group associated
        with it is not the default authority—i.e. this is a third-party group.

        :arg appstruct: Data, which may or may not contain a ``groupid`` entry
        :type appstruct: dict
        :raise h.schemas.ValidationError:

        """
        groupid = appstruct.get("groupid", None)
        if groupid is None:  # Nothing to validate
            return

        if (self.group_authority is None) or (
            self.group_authority == self.default_authority
        ):
            # This is a first-party group
            raise ValidationError(
                # pylint:disable=consider-using-f-string
                "{err_msg} '{authority}'".format(
                    err_msg=_(
                        "groupid may only be set on groups outside of the default authority"
                    ),
                    authority=self.default_authority,
                )
            )

        groupid_parts = split_groupid(groupid)

        if groupid_parts["authority"] != self.group_authority:
            # The authority part of the ``groupid`` doesn't match the
            # group's authority
            raise ValidationError(
                # pylint:disable=consider-using-f-string
                "{err_msg} '{groupid}'".format(
                    err_msg=_("Invalid authority specified in groupid"), groupid=groupid
                )
            )

    @staticmethod
    def _whitelisted_fields_only(appstruct):
        """Return a new appstruct containing only schema-defined fields."""

        new_appstruct = {}

        for allowed_field in GROUP_SCHEMA_PROPERTIES:
            if allowed_field in appstruct:
                new_appstruct[allowed_field] = appstruct[allowed_field]

        return new_appstruct


class CreateGroupAPISchema(GroupAPISchema):
    """Schema for validating create-group API data."""

    schema = {
        "type": "object",
        "properties": GROUP_SCHEMA_PROPERTIES,
        "required": ["name"],  # ``name`` is a required field when creating
    }


class UpdateGroupAPISchema(GroupAPISchema):
    """
    Class for validating update-group API data.

    Currently identical to base schema
    """
