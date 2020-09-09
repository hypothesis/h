from h import models


def test_is_blocked(db_session):
    db_session.add(models.Blocklist(uri="http://example.com"))
    db_session.add(models.Blocklist(uri="http://example.com/bar"))
    db_session.flush()

    assert models.Blocklist.is_blocked(db_session, "http://example.com")
    assert models.Blocklist.is_blocked(db_session, "http://example.com/bar")
    assert not models.Blocklist.is_blocked(db_session, "http://example.com/foo")


def test_is_blocked_with_wildcards(db_session):
    db_session.add(models.Blocklist(uri="%//example.com%"))
    db_session.flush()

    assert models.Blocklist.is_blocked(db_session, "http://example.com/")
    assert models.Blocklist.is_blocked(db_session, "http://example.com/bar")
    assert models.Blocklist.is_blocked(db_session, "http://example.com/foo")
