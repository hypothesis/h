import datetime
from unittest.mock import create_autospec

import pytest
from h_matchers import Any
from pyramid import security

from h.formatters import AnnotationFlagFormatter
from h.presenters.annotation_json import AnnotationJSONPresenter
from h.traversal import AnnotationContext


class TestAnnotationJSONPresenter:
    def test_asdict(self, annotation, context, DocumentJSONPresenter):
        annotation.created = datetime.datetime(2016, 2, 24, 18, 3, 25, 768)
        annotation.updated = datetime.datetime(2016, 2, 29, 10, 24, 5, 564)
        annotation.references = ["referenced-id-1", "referenced-id-2"]
        annotation.extra = {"extra-1": "foo", "extra-2": "bar"}
        presenter = AnnotationJSONPresenter(context)

        result = presenter.asdict()

        assert result == Any.dict.containing(
            {
                "id": annotation.id,
                "created": "2016-02-24T18:03:25.000768+00:00",
                "updated": "2016-02-29T10:24:05.000564+00:00",
                "user": annotation.userid,
                "uri": annotation.target_uri,
                "group": annotation.groupid,
                "text": annotation.text,
                "tags": annotation.tags,
                "permissions": {
                    "read": [annotation.userid],
                    "admin": [annotation.userid],
                    "update": [annotation.userid],
                    "delete": [annotation.userid],
                },
                "target": [
                    {
                        "source": annotation.target_uri,
                        "selector": annotation.target_selectors,
                    }
                ],
                "document": DocumentJSONPresenter.return_value.asdict.return_value,
                "links": context.links,
                "references": annotation.references,
                "extra-1": "foo",
                "extra-2": "bar",
            }
        )

        DocumentJSONPresenter.assert_called_once_with(annotation.document)
        DocumentJSONPresenter.return_value.asdict.assert_called_once_with()

    def test_asdict_extra_inherits_correctly(self, annotation, context):
        annotation.extra = {"id": "DIFFERENT"}

        presented = AnnotationJSONPresenter(context).asdict()

        # We can't override things (we are applied first)
        assert presented["id"] == annotation.id
        # And we aren't mutated
        assert annotation.extra == {"id": "DIFFERENT"}

    def test_asdict_merges_formatters(self, annotation, context, get_formatter):
        formatters = [
            get_formatter({"flagged": "nope"}),
            get_formatter({"nipsa": "maybe"}),
        ]

        presented = AnnotationJSONPresenter(context, formatters=formatters).asdict()

        assert presented["flagged"] == "nope"
        assert presented["nipsa"] == "maybe"

        for formatter in formatters:
            formatter.format.assert_called_once_with(context)

    @pytest.mark.parametrize(
        "shared,readable_by,permission_template",
        (
            (False, [], "{annotation.userid}"),
            (True, [], "group:{annotation.groupid}"),
            (True, [security.Everyone], "group:__world__"),
        ),
    )
    def test_read_permission(
        self,
        annotation,
        context,
        principals_allowed_by_permission,
        shared,
        readable_by,
        permission_template,
    ):
        annotation.shared = shared
        principals_allowed_by_permission.return_value = readable_by

        presented = AnnotationJSONPresenter(context).asdict()

        permission = permission_template.format(annotation=annotation)
        assert presented["permissions"]["read"] == [permission]

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation(groupid="NOT WORLD")

    @pytest.fixture
    def context(self, annotation):
        return create_autospec(
            AnnotationContext, instance=True, spec_set=True, annotation=annotation
        )

    @pytest.fixture
    def get_formatter(self):
        def get_formatter(payload=None):
            # All formatters should have the same interface. We'll pick one at
            # random to act as an exemplar
            formatter = create_autospec(
                AnnotationFlagFormatter, spec_set=True, instance=True
            )
            formatter.format.return_value = payload or {}
            return formatter

        return get_formatter

    @pytest.fixture
    def DocumentJSONPresenter(self, patch):
        return patch("h.presenters.annotation_json.DocumentJSONPresenter")

    @pytest.fixture
    def principals_allowed_by_permission(self, patch):
        return patch("h.presenters.annotation_json.principals_allowed_by_permission")
