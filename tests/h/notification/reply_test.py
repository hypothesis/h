# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import mock

from h.models import Annotation
from h.models import Document, DocumentMeta
from h.models import Subscriptions
from h.notification.reply import Notification
from h.notification.reply import get_notification
from h.services.user import UserService

FIXTURE_DATA = {
    "reply": {
        "id": "OECV3AmDEeaAtTt8rjCjIg",
        "groupid": "__world__",
        "shared": True,
        "userid": "acct:elephant@safari.net",
    },
    "parent": {
        "id": "SucHcAmDEeaAtf_ZeH-rhA",
        "groupid": "__world__",
        "shared": True,
        "userid": "acct:giraffe@safari.net",
    },
}


@pytest.mark.usefixtures(
    "authz_policy", "fetch_annotation", "subscription", "user_service"
)
class TestGetNotification(object):
    def test_returns_correct_params_when_subscribed(
        self, parent, pyramid_request, reply, user_service
    ):
        result = get_notification(pyramid_request, reply, "create")

        assert isinstance(result, Notification)
        assert result.reply == reply
        assert result.parent == parent
        assert result.reply_user == user_service.fetch(reply.userid)
        assert result.parent_user == user_service.fetch(parent.userid)
        assert result.document == reply.document

    def test_returns_none_when_action_is_not_create(self, pyramid_request, reply):
        assert get_notification(pyramid_request, reply, "update") is None
        assert get_notification(pyramid_request, reply, "delete") is None
        assert get_notification(pyramid_request, reply, "frobnicate") is None

    def test_returns_none_when_annotation_is_not_reply(self, pyramid_request, reply):
        reply.references = None

        result = get_notification(pyramid_request, reply, "create")

        assert result is None

    def test_returns_none_when_parent_does_not_exist(
        self, annotations, parent, pyramid_request, reply
    ):
        del annotations[parent.id]

        result = get_notification(pyramid_request, reply, "create")

        assert result is None

    def test_returns_none_when_parent_user_does_not_exist(
        self, factories, pyramid_request, reply, user_service
    ):
        users = {"acct:elephant@safari.net": factories.User()}
        user_service.fetch.side_effect = users.get

        result = get_notification(pyramid_request, reply, "create")

        assert result is None

    def test_returns_none_when_parent_user_has_no_email_address(
        self, factories, pyramid_request, reply, user_service
    ):
        users = {
            "acct:giraffe@safari.net": factories.User(email=None),
            "acct:elephant@safari.net": factories.User(),
        }
        user_service.fetch.side_effect = users.get

        assert get_notification(pyramid_request, reply, "create") is None

    def test_returns_none_when_reply_user_does_not_exist(
        self, factories, pyramid_request, reply, user_service
    ):
        """
        Don't send a reply if somehow the replying user ceased to exist.

        It's not clear when or why this would ever happen, but we can't
        construct the reply email without the user who replied existing. We log
        a warning if this happens.
        """
        users = {"acct:giraffe@safari.net": factories.User()}
        user_service.fetch.side_effect = users.get

        result = get_notification(pyramid_request, reply, "create")

        assert result is None

    def test_returns_none_when_reply_by_same_user(self, parent, pyramid_request, reply):
        parent.userid = "acct:elephant@safari.net"

        result = get_notification(pyramid_request, reply, "create")

        assert result is None

    def test_returns_none_when_parent_user_cannot_read_reply(
        self, pyramid_request, reply
    ):
        reply.shared = False

        result = get_notification(pyramid_request, reply, "create")

        assert result is None

    def test_returns_none_when_subscription_inactive(
        self, pyramid_request, reply, subscription
    ):
        subscription.active = False

        result = get_notification(pyramid_request, reply, "create")

        assert result is None

    def test_returns_none_when_subscription_absent(
        self, db_session, parent, pyramid_request, reply
    ):
        db_session.query(Subscriptions).delete()

        result = get_notification(pyramid_request, reply, "create")

        assert result is None

    @pytest.fixture
    def annotations(self):
        return {}

    @pytest.fixture
    def authz_policy(self, pyramid_config):
        from pyramid.authorization import ACLAuthorizationPolicy

        pyramid_config.set_authorization_policy(ACLAuthorizationPolicy())

    @pytest.fixture
    def fetch_annotation(self, patch, annotations):
        fetch_annotation = patch("h.notification.reply.storage.fetch_annotation")
        fetch_annotation.side_effect = lambda _, id: annotations.get(id)
        return fetch_annotation

    @pytest.fixture
    def parent(self, annotations):
        parent = Annotation(**FIXTURE_DATA["parent"])
        annotations[parent.id] = parent
        return parent

    @pytest.fixture
    def reply(self, annotations, db_session, parent):
        # We need to create a document object to provide the title, and
        # ensure it is associated with the annotation through the
        # annotation's `target_uri`
        doc = Document.find_or_create_by_uris(
            db_session, claimant_uri="http://example.net/foo", uris=[]
        ).one()
        doc.meta.append(
            DocumentMeta(
                type="title", value=["Some document"], claimant="http://example.com/foo"
            )
        )
        reply = Annotation(**FIXTURE_DATA["reply"])
        reply.target_uri = "http://example.net/foo"
        reply.references = [parent.id]
        reply.document = doc
        db_session.add(reply)
        db_session.flush()
        annotations[reply.id] = reply
        return reply

    @pytest.fixture
    def subscription(self, db_session):
        sub = Subscriptions(type="reply", active=True, uri="acct:giraffe@safari.net")
        db_session.add(sub)
        db_session.flush()
        return sub

    @pytest.fixture
    def user_service(self, factories, pyramid_config):
        user_service = mock.create_autospec(UserService, spec_set=True, instance=True)

        users = {
            "acct:giraffe@safari.net": factories.User(),
            "acct:elephant@safari.net": factories.User(),
        }
        user_service.fetch.side_effect = users.get

        pyramid_config.register_service(user_service, name="user")
        return user_service
