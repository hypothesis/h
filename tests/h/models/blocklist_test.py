import pytest

from h.models.blocklist import Blocklist


class TestBlocklist:
    @pytest.mark.parametrize(
        "block_uri,uri,is_blocked",
        (
            ("http://example.com", "http://example.com", True),
            ("http://example.com/path", "http://example.com/path", True),
            (None, "http://example.com", False),
            ("%//example.com%", "http://example.com", True),
            ("%//example.com%", "http://example.com/path", True),
        ),
    )
    def test_is_blocked(self, db_session, block_uri, uri, is_blocked):
        if block_uri:
            db_session.add(Blocklist(uri=block_uri))

        assert Blocklist.is_blocked(db_session, uri) == is_blocked

    def test___repr__(self):
        blocklist = Blocklist(uri="http://example.com")

        assert repr(blocklist) == "http://example.com"
