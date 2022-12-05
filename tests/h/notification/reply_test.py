import pytest

from h.models import Annotation, Document, DocumentMeta, Subscriptions
from h.notification.reply import Notification, get_notification

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


class TestGetNotification:
    def test_returns_correct_params_when_subscribed(
        self, parent, pyramid_request, reply, user_service, subscription_service
    ):
        result = get_notification(pyramid_request, reply, "create")

        subscription_service.get_subscription.assert_called_once_with(
            user_id=parent.userid, type_=Subscriptions.Type.REPLY
        )

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

        assert get_notification(pyramid_request, reply, "create") is None

    def test_returns_none_when_parent_does_not_exist(
        self, annotations, parent, pyramid_request, reply
    ):
        del annotations[parent.id]

        assert get_notification(pyramid_request, reply, "create") is None

    def test_returns_none_when_parent_user_does_not_exist(
        self, factories, pyramid_request, reply, user_service
    ):
        users = {"acct:elephant@safari.net": factories.User()}
        user_service.fetch.side_effect = users.get

        assert get_notification(pyramid_request, reply, "create") is None

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

        assert get_notification(pyramid_request, reply, "create") is None

    def test_returns_none_when_reply_by_same_user(self, parent, pyramid_request, reply):
        parent.userid = "acct:elephant@safari.net"

        assert get_notification(pyramid_request, reply, "create") is None

    def test_returns_none_when_parent_user_cannot_read_reply(
        self, pyramid_request, reply
    ):
        reply.shared = False

        assert get_notification(pyramid_request, reply, "create") is None

    def test_returns_none_when_subscription_inactive(
        self, pyramid_request, reply, subscription_service
    ):
        subscription_service.get_subscription.return_value.active = False

        assert get_notification(pyramid_request, reply, "create") is None

    @pytest.fixture
    def annotations(self):
        return {}

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

    @pytest.fixture(autouse=True)
    def fetch_annotation(self, patch, annotations):
        fetch_annotation = patch("h.notification.reply.storage.fetch_annotation")
        fetch_annotation.side_effect = lambda _, id: annotations.get(id)
        return fetch_annotation

    @pytest.fixture(autouse=True)
    def subscription_service(self, subscription_service, factories):
        subscription_service.get_subscription.return_value = factories.Subscriptions(
            active=True, type=Subscriptions.Type.REPLY.value
        )
        return subscription_service

    @pytest.fixture(autouse=True)
    def user_service(self, user_service, factories):
        users = {
            "acct:giraffe@safari.net": factories.User(),
            "acct:elephant@safari.net": factories.User(),
        }
        user_service.fetch.side_effect = users.get
        return user_service
