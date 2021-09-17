from gevent.monkey import MonkeyPatchWarning, patch_all

# We want to patch as early as possible, which totally ruins the import order
try:
    patch_all()
except MonkeyPatchWarning:
    pass

import json  # pylint: disable=wrong-import-position,wrong-import-order
from collections import (  # pylint: disable=wrong-import-position,wrong-import-order
    defaultdict,
)
from json import (  # pylint: disable=wrong-import-position,wrong-import-order
    JSONDecodeError,
)

import gevent  # pylint: disable=wrong-import-position
import pytest  # pylint: disable=wrong-import-position
from h_matchers import Any  # pylint: disable=wrong-import-position
from ws4py.client.geventclient import (  # pylint: disable=wrong-import-position
    WebSocketClient,
)


class Client(WebSocketClient):
    def __init__(self, url, message_queue):
        super().__init__(
            url=url,
            protocols=["http-only", "chat"],
        )
        self.connect()

        self.message_queue = message_queue
        self.threads = []

    def expect_messages(self, client_id, num=1):
        def _capture_incoming():
            messages_received = 0

            while True:
                message = self.receive()
                if message is not None:
                    try:
                        data = json.loads(message.data)
                    except JSONDecodeError:
                        data = message.data

                    self.message_queue[client_id].append(data)

                    messages_received += 1
                    if messages_received == num:
                        self.close()
                        break
                else:
                    print("Disconnect")
                    break

                gevent.sleep()

        self.threads.append(gevent.spawn(_capture_incoming))

    def login(self, client_id):
        for message in [
            {
                "filter": {
                    "match_policy": "include_any",
                    "clauses": [
                        {
                            "field": "/uri",
                            "operator": "one_of",
                            "value": ["https://example.com/"],
                            "case_sensitive": False,
                        }
                    ],
                    "actions": {"create": True, "update": True, "delete": True},
                }
            },
            {"messageType": "client_id", "value": client_id},
            {"type": "whoami", "id": 1},
        ]:
            self.send(json.dumps(message))

    def wait_on_client(self):
        self.wait_for([self])

    @classmethod
    def wait_for(cls, clients, timeout=1):
        try:
            threads = []
            for client in clients:
                threads.extend(client.threads)

            gevent.joinall(threads, timeout=timeout)

        finally:
            for client in clients:
                client.close()


@pytest.mark.usefixtures("ws_app")
class TestWebSocket:
    def test_missing_pages(self, ws_app):
        response = ws_app.get("/not_a_path", status=404)

        assert response.json == {
            "ok": False,
            "error": "not_found",
            "reason": "These are not the droids you are looking for.",
        }

    def test_we_can_connect(self, client, messages, user):
        client.expect_messages(client_id="user_client", num=1)
        client.login("user_client")

        client.wait_on_client()

        assert messages == {
            "user_client": [
                {"ok": True, "reply_to": 1, "type": "whoyouare", "userid": user.userid}
            ]
        }

    def test_we_can_pass_messages(
        self, app, client, auth_token, anonymous_client, messages
    ):
        client.expect_messages(client_id="user_client", num=2)
        client.login("user_client")
        anonymous_client.expect_messages(client_id="anon_client", num=2)
        anonymous_client.login("anon_client")

        # Create a public annotation the anonymous user can see
        app.post_json(
            "/api/annotations",
            {
                "group": "__world__",
                "permissions": {"read": ["group:__world__"]},
                "text": "My annotation",
                "uri": "http://example.com",
            },
            headers={"Authorization": f"Bearer {auth_token.value}"},
            status=200,
        )

        Client.wait_for([client, anonymous_client])

        assert messages["user_client"] == [
            Any.dict.containing({"type": "whoyouare"}),
            Any.dict.containing({"type": "annotation-notification"}),
        ]

        assert messages["anon_client"] == [
            Any.dict.containing({"type": "whoyouare"}),
            Any.dict.containing({"type": "annotation-notification"}),
        ]

    @pytest.fixture
    def user(self, factories, db_session):
        user = factories.User()
        db_session.commit()
        return user

    @pytest.fixture
    def auth_token(self, user, factories, db_session):
        auth_token = factories.OAuth2Token(userid=user.userid)
        db_session.commit()
        return auth_token

    @pytest.fixture
    def messages(self):
        return defaultdict(list)

    @pytest.fixture
    def client(self, auth_token, messages):
        client = None
        try:
            client = Client(
                url=f"ws://localhost:5001/ws?access_token={auth_token.value}",
                message_queue=messages,
            )
            yield client
        finally:
            if client:
                client.wait_on_client()

    @pytest.fixture
    def anonymous_client(self, messages):
        client = None
        try:
            client = Client(
                url="ws://localhost:5001/ws",
                message_queue=messages,
            )
            yield client
        finally:
            if client:
                client.wait_on_client()
