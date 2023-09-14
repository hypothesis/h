"""Classes for validating data passed to the annotations API."""
import copy

import colander
from dateutil.parser import parse
from pyramid import i18n

from h.schemas.base import JSONSchema, ValidationError
from h.search.query import LIMIT_DEFAULT, LIMIT_MAX, OFFSET_MAX
from h.search.util import wildcard_uri_is_valid
from h.util import document_claims

_ = i18n.TranslationStringFactory(__package__)


def _validate_wildcard_uri(node, value):
    """Raise if wildcards are within the domain of the uri."""
    for val in value:
        if not wildcard_uri_is_valid(val):
            raise colander.Invalid(
                node,
                """Wildcards (_ and *) are not permitted within the
                domain of wildcard_uri""",
            )


DOCUMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "dc": {
            "type": "object",
            "properties": {
                "identifier": {"type": "array", "items": {"type": "string"}}
            },
        },
        "highwire": {
            "type": "object",
            "properties": {
                "doi": {"type": "array", "items": {"type": "string"}},
                "pdf_url": {"type": "array", "items": {"type": "string"}},
            },
        },
        "link": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "href": {"type": "string"},
                    "type": {"type": "string"},
                },
                "required": ["href"],
            },
        },
    },
}


SELECTOR_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {"type": {"type": "string"}},
        "required": ["type"],
    },
}


class AnnotationSchema(JSONSchema):
    """Validate an annotation object."""

    schema = {
        "type": "object",
        "properties": {
            "document": copy.deepcopy(DOCUMENT_SCHEMA),
            "group": {"type": "string"},
            "permissions": {
                "title": "Permissions",
                "description": "Annotation action access control list",
                "type": "object",
                "patternProperties": {
                    "^(admin|delete|read|update)$": {
                        "type": "array",
                        "items": {"type": "string", "pattern": "^(acct:|group:).+$"},
                    }
                },
                "required": ["read"],
            },
            "references": {"type": "array", "items": {"type": "string"}},
            "tags": {"type": "array", "items": {"type": "string"}},
            "target": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"selector": copy.deepcopy(SELECTOR_SCHEMA)},
                },
            },
            "text": {"type": "string"},
            "uri": {"type": "string"},
            "metadata": {"type": "object"},
        },
    }


class URLMigrationSchema(JSONSchema):
    """Validate a URL migration request."""

    schema_version = 7  # Required for `propertyNames`

    schema = {
        "type": "object",
        # The restriction to HTTP(S) URLs is just to help catch mistakes
        # in the input. We could relax this constraint if needed.
        "propertyNames": {"pattern": "^https?:"},
        "patternProperties": {
            "": {
                "type": "object",
                "required": ["url"],
                "properties": {
                    "url": {"type": "string", "pattern": "^https?:"},
                    "document": copy.deepcopy(DOCUMENT_SCHEMA),
                    "selectors": copy.deepcopy(SELECTOR_SCHEMA),
                },
            }
        },
    }


class CreateAnnotationSchema:
    """Validate the POSTed data of a create annotation request."""

    def __init__(self, request):
        self.structure = AnnotationSchema()
        self.request = request

    def validate(self, data):
        appstruct = self.structure.validate(data)

        new_appstruct = {}

        _remove_protected_fields(appstruct)

        new_appstruct["userid"] = self.request.authenticated_userid

        uri = appstruct.pop("uri", "").strip()
        if not uri:
            raise ValidationError("uri: " + _("'uri' is a required property"))
        new_appstruct["target_uri"] = uri

        new_appstruct["text"] = appstruct.pop("text", "")
        new_appstruct["tags"] = appstruct.pop("tags", [])
        new_appstruct["groupid"] = appstruct.pop("group", "__world__")
        new_appstruct["references"] = appstruct.pop("references", [])

        if "permissions" in appstruct:
            new_appstruct["shared"] = _shared(
                appstruct.pop("permissions"), new_appstruct["groupid"]
            )
        else:
            new_appstruct["shared"] = False

        if "target" in appstruct:
            new_appstruct["target_selectors"] = _target_selectors(
                appstruct.pop("target")
            )

        # Replies always get the same groupid as their parent. The parent's
        # groupid is added to the reply annotation later by the storage code.
        # Here we just delete any group sent by the client from replies.
        if new_appstruct["references"] and "groupid" in new_appstruct:
            del new_appstruct["groupid"]

        new_appstruct["document"] = transform_document(
            appstruct.pop("document", {}), new_appstruct["target_uri"]
        )

        new_appstruct["metadata"] = appstruct.pop("metadata", None)

        new_appstruct["extra"] = appstruct

        return new_appstruct


class UpdateAnnotationSchema:
    """Validate the POSTed data of an update annotation request."""

    def __init__(self, request, existing_target_uri, groupid):
        self.request = request
        self.existing_target_uri = existing_target_uri
        self.groupid = groupid
        self.structure = AnnotationSchema()

    def validate(self, data):
        appstruct = self.structure.validate(data)

        new_appstruct = {}

        _remove_protected_fields(appstruct)

        # Some fields are not allowed to be changed in annotation updates.
        for key in ["group", "groupid", "userid", "references"]:
            appstruct.pop(key, "")

        # Fields that are allowed to be updated and that have a different name
        # internally than in the public API.
        if "uri" in appstruct:
            new_uri = appstruct.pop("uri").strip()
            if not new_uri:
                raise ValidationError("uri: " + _("'uri' is a required property"))
            new_appstruct["target_uri"] = new_uri

        if "permissions" in appstruct:
            new_appstruct["shared"] = _shared(
                appstruct.pop("permissions"), self.groupid
            )

        if "target" in appstruct:
            new_appstruct["target_selectors"] = _target_selectors(
                appstruct.pop("target")
            )

        # Fields that are allowed to be updated and that have the same internal
        # and external name.
        for key in ["text", "tags"]:
            if key in appstruct:
                new_appstruct[key] = appstruct.pop(key)

        if "document" in appstruct:
            new_appstruct["document"] = transform_document(
                appstruct.pop("document"),
                new_appstruct.get("target_uri", self.existing_target_uri),
            )

        new_appstruct["metadata"] = appstruct.pop("metadata", None)

        new_appstruct["extra"] = appstruct

        return new_appstruct


def transform_document(document, claimant):
    """
    Return document meta and document URI data from the given document dict.

    Transforms the "document" dict that the client posts into a convenient
    format for creating DocumentURI and DocumentMeta objects later.

    """
    document = document or {}
    document_uri_dicts = document_claims.document_uris_from_data(
        copy.deepcopy(document), claimant=claimant
    )
    document_meta_dicts = document_claims.document_metas_from_data(
        copy.deepcopy(document), claimant=claimant
    )
    return {
        "document_uri_dicts": document_uri_dicts,
        "document_meta_dicts": document_meta_dicts,
    }


def _remove_protected_fields(appstruct):
    # Some fields are not to be set by the user, ignore them.
    for field in [
        "created",
        "updated",
        "user",
        "id",
        "links",
        "flagged",
        "hidden",
        "moderation",
        "user_info",
    ]:
        appstruct.pop(field, None)


def _shared(permissions, groupid):
    """
    Return True if the given permissions object represents shared permissions.

    Return False otherwise.

    Reduces the client's complex permissions dict to a simple shared boolean.

    :param permissions: the permissions dict sent by the client in an
        annotation create or update request
    :type permissions: dict

    :param groupid: the groupid of the annotation that the permissions dict
        applies to
    :type groupid: unicode

    """
    return permissions["read"] == [f"group:{groupid}"]


def _target_selectors(targets):
    """
    Return the target selectors from the given target list.

    Transforms the target lists that the client sends in annotation create and
    update requests into our internal target_selectors format.

    """
    # Any targets other than the first in the list are discarded.
    # Any fields of the target other than 'selector' are discarded.
    if targets and "selector" in targets[0]:
        return targets[0]["selector"]

    return []


class SearchParamsSchema(colander.Schema):
    _separate_replies = colander.SchemaNode(
        colander.Boolean(),
        missing=False,
        description="Return a separate set of annotations and their replies.",
    )
    sort = colander.SchemaNode(
        colander.String(),
        validator=colander.OneOf(["created", "updated", "group", "id", "user"]),
        missing="updated",
        description="The field by which annotations should be sorted.",
    )
    search_after = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        description="""Returns results after the annotation who's sort field
                    has this value. If specifying a date use the format
                    yyyy-MM-dd'T'HH:mm:ss.SSX or time in miliseconds since the
                    epoch. This is used for iteration through large collections
                    of results.""",
    )
    limit = colander.SchemaNode(
        colander.Integer(),
        validator=colander.Range(min=0, max=LIMIT_MAX),
        missing=LIMIT_DEFAULT,
        description="The maximum number of annotations to return.",
    )
    order = colander.SchemaNode(
        colander.String(),
        validator=colander.OneOf(["asc", "desc"]),
        missing="desc",
        description="The direction of sort.",
    )
    offset = colander.SchemaNode(
        colander.Integer(),
        validator=colander.Range(min=0, max=OFFSET_MAX),
        missing=0,
        description="""The number of initial annotations to skip. This is
                       used for pagination. Not suitable for paging through
                       thousands of annotations-search_after should be used
                       instead.""",
    )
    group = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(colander.String()),
        missing=colander.drop,
        description="Limit the results to this group of annotations.",
    )
    quote = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(colander.String()),
        missing=colander.drop,
        description="""Limit the results to annotations that contain this text inside
                        the text that was annotated.""",
    )
    references = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(colander.String()),
        missing=colander.drop,
        description="""Returns annotations that are replies to this parent annotation id.""",
    )
    tag = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(colander.String()),
        missing=colander.drop,
        description="Limit the results to annotations tagged with the specified value.",
    )
    tags = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(colander.String()),
        missing=colander.drop,
        description="Alias of tag.",
    )
    text = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(colander.String()),
        missing=colander.drop,
        description="Limit the results to annotations that contain this text in their textual body.",
    )
    uri = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(colander.String()),
        missing=colander.drop,
        description="""Limit the results to annotations matching the specific URI
                       or equivalent URIs. URI can be a URL (a web page address) or
                       a URN representing another kind of resource such as DOI
                       (Digital Object Identifier) or a PDF fingerprint.""",
    )
    uri_parts = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(colander.String()),
        name="uri.parts",
        missing=colander.drop,
        description="""Limit the results to annotations with the given keyword
                       appearing in the URL.""",
    )
    url = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(colander.String()),
        missing=colander.drop,
        description="Alias of uri.",
    )
    wildcard_uri = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(colander.String()),
        validator=_validate_wildcard_uri,
        missing=colander.drop,
        description="""
            Limit the results to annotations matching the wildcard URI.
            URI can be a URL (a web page address) or a URN representing another
            kind of resource such as DOI (Digital Object Identifier) or a
            PDF fingerprint.

            `*` will match any character sequence (including an empty one),
            and a `_` will match any single character. Wildcards are only permitted
            within the path and query parts of the URI.

            Escaping wildcards is not supported.

            Examples of valid uris":" `http://foo.com/*` `urn:x-pdf:*` `file://localhost/_bc.pdf`
            Examples of invalid uris":" `*foo.com` `u_n:*` `file://*` `http://foo.com*`
            """,
    )
    any = colander.SchemaNode(
        colander.Sequence(),
        colander.SchemaNode(colander.String()),
        missing=colander.drop,
        description="""Limit the results to annotations whose quote, tags,
                       text or url fields contain this keyword.""",
    )
    user = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        description="Limit the results to annotations made by the specified user.",
    )

    def validator(self, node, cstruct):
        sort = cstruct["sort"]
        search_after = cstruct.get("search_after", None)

        if search_after:
            if sort in ["updated", "created"] and not self._date_is_parsable(
                search_after
            ):
                raise colander.Invalid(
                    node,
                    """search_after must be a parsable date in the form
                    yyyy-MM-dd'T'HH:mm:ss.SSX
                    or time in miliseconds since the epoch.""",
                )

            # offset must be set to 0 if search_after is specified.
            cstruct["offset"] = 0

    @staticmethod
    def _date_is_parsable(value):
        """Return True if date is parsable and False otherwise."""

        # Dates like "2017" can also be cast as floats so if a number is less
        # than 9999 it is assumed to be a year and not ms since the epoch.
        try:  # pylint: disable=too-many-try-statements
            if float(value) < 9999:
                raise ValueError("This is not in the form ms since the epoch.")
        except ValueError:
            try:
                parse(value)
            except ValueError:
                return False
        return True
