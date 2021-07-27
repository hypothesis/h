import datetime
from unittest import mock
from unittest.mock import create_autospec

import pytest
from pyramid import security
from pyramid.authorization import ACLAuthorizationPolicy

from h.formatters import AnnotationFlagFormatter
from h.presenters.annotation_json import AnnotationJSONPresenter
from h.security.permissions import Permission
from h.traversal import AnnotationContext


class TestAnnotationJSONPresenter:
    def test_asdict(self, document_asdict, groupfinder_service, links_service):
        ann = mock.Mock(
            id="the-id",
            created=datetime.datetime(2016, 2, 24, 18, 3, 25, 768),
            updated=datetime.datetime(2016, 2, 29, 10, 24, 5, 564),
            userid="acct:luke",
            target_uri="http://example.com",
            text="It is magical!",
            tags=["magic"],
            groupid="__world__",
            shared=True,
            target_selectors=[{"TestSelector": "foobar"}],
            references=["referenced-id-1", "referenced-id-2"],
            extra={"extra-1": "foo", "extra-2": "bar"},
        )
        context = AnnotationContext(ann, groupfinder_service, links_service)

        document_asdict.return_value = {"foo": "bar"}

        expected = {
            "id": "the-id",
            "created": "2016-02-24T18:03:25.000768+00:00",
            "updated": "2016-02-29T10:24:05.000564+00:00",
            "user": "acct:luke",
            "uri": "http://example.com",
            "text": "It is magical!",
            "tags": ["magic"],
            "group": "__world__",
            "permissions": {
                "read": ["group:__world__"],
                "admin": ["acct:luke"],
                "update": ["acct:luke"],
                "delete": ["acct:luke"],
            },
            "target": [
                {
                    "source": "http://example.com",
                    "selector": [{"TestSelector": "foobar"}],
                }
            ],
            "document": {"foo": "bar"},
            "links": links_service.get_all.return_value,
            "references": ["referenced-id-1", "referenced-id-2"],
            "extra-1": "foo",
            "extra-2": "bar",
        }

        result = AnnotationJSONPresenter(context).asdict()

        assert result == expected

    def test_asdict_extra_cannot_override_other_data(
        self, document_asdict, groupfinder_service, links_service
    ):
        ann = mock.Mock(id="the-real-id", extra={"id": "the-extra-id"})
        context = AnnotationContext(ann, groupfinder_service, links_service)
        document_asdict.return_value = {}

        presented = AnnotationJSONPresenter(context).asdict()
        assert presented["id"] == "the-real-id"

    def test_asdict_extra_uses_copy_of_extra(
        self, document_asdict, groupfinder_service, links_service
    ):
        extra = {"foo": "bar"}
        ann = mock.Mock(id="my-id", extra=extra)
        context = AnnotationContext(ann, groupfinder_service, links_service)
        document_asdict.return_value = {}

        AnnotationJSONPresenter(context).asdict()

        # Presenting the annotation shouldn't change the "extra" dict.
        assert extra == {"foo": "bar"}

    def test_asdict_merges_formatters(
        self, groupfinder_service, links_service, get_formatter
    ):
        ann = mock.Mock(id="the-real-id", extra={})
        context = AnnotationContext(ann, groupfinder_service, links_service)
        presenter = AnnotationJSONPresenter(
            context,
            formatters=[
                get_formatter({"flagged": "nope"}),
                get_formatter({"nipsa": "maybe"}),
            ],
        )

        presented = presenter.asdict()

        assert presented["flagged"] == "nope"
        assert presented["nipsa"] == "maybe"

    def test_immutable_formatters(
        self, groupfinder_service, links_service, get_formatter
    ):
        """Double-check we can't mutate the formatters list after the fact.

        This is an extra check just to make sure we can't accidentally change
        the constructor so that it simply aliases the list that's passed in,
        leaving us open to all kinds of mutability horrors.

        """
        ann = mock.Mock(id="the-real-id", extra={})
        context = AnnotationContext(ann, groupfinder_service, links_service)
        formatters = []

        presenter = AnnotationJSONPresenter(context, formatters)
        formatters.append(get_formatter({"enterprise": "synergy"}))
        presented = presenter.asdict()

        assert "enterprise" not in presented

    def test_formatter_uses_annotation_context(
        self, groupfinder_service, links_service, get_formatter
    ):
        annotation = mock.Mock(id="the-id", extra={})
        context = AnnotationContext(annotation, groupfinder_service, links_service)
        formatter = get_formatter()

        presenter = AnnotationJSONPresenter(context, formatters=[formatter])
        presenter.asdict()

        formatter.format.assert_called_once_with(context)

    @pytest.mark.usefixtures("policy")
    @pytest.mark.parametrize(
        "annotation,group_readable,action,expected",
        [
            (
                mock.Mock(userid="acct:luke", shared=False),
                "world",
                "read",
                ["acct:luke"],
            ),
            (
                mock.Mock(userid="acct:luke", groupid="abcde", shared=False),
                "members",
                "read",
                ["acct:luke"],
            ),
            (
                mock.Mock(groupid="__world__", shared=True),
                "world",
                "read",
                ["group:__world__"],
            ),
            (
                mock.Mock(groupid="lulapalooza", shared=True),
                "members",
                "read",
                ["group:lulapalooza"],
            ),
            (
                mock.Mock(groupid="open", shared=True),
                "world",
                "read",
                ["group:__world__"],
            ),
            (mock.Mock(userid="acct:luke"), None, "admin", ["acct:luke"]),
            (mock.Mock(userid="acct:luke"), None, "update", ["acct:luke"]),
            (mock.Mock(userid="acct:luke"), None, "delete", ["acct:luke"]),
        ],
    )
    def test_permissions(
        self,
        annotation,
        group_readable,
        action,
        expected,
        groupfinder_service,
        links_service,
    ):
        annotation.deleted = False

        group_principals = {
            "members": (
                security.Allow,
                "group:{}".format(annotation.groupid),
                Permission.Group.READ,
            ),
            "world": (security.Allow, security.Everyone, Permission.Group.READ),
            None: security.DENY_ALL,
        }
        group = mock.Mock(spec_set=["__acl__"])
        group.__acl__.return_value = [group_principals[group_readable]]
        groupfinder_service.find.return_value = group

        context = AnnotationContext(annotation, groupfinder_service, links_service)
        presenter = AnnotationJSONPresenter(context)
        assert expected == presenter.permissions[action]

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
    def policy(self, pyramid_config):
        """Set up a fake authentication policy with a real ACL authorization policy."""
        policy = ACLAuthorizationPolicy()
        pyramid_config.testing_securitypolicy(None)
        pyramid_config.set_authorization_policy(policy)

    @pytest.fixture
    def document_asdict(self, patch):
        return patch("h.presenters.annotation_json.DocumentJSONPresenter.asdict")
