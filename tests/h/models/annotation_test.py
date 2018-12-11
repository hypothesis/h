# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.models.annotation import Annotation


def test_parent_id_of_direct_reply():
    ann = Annotation(references=["parent_id"])

    assert ann.parent_id == "parent_id"


def test_parent_id_of_reply_to_reply():
    ann = Annotation(references=["reply1", "reply2", "parent_id"])

    assert ann.parent_id == "parent_id"


def test_reply_is_reply():
    ann = Annotation(references=["parent_id"])

    assert ann.is_reply is True


def test_non_reply_is_not_reply():
    ann = Annotation()

    assert ann.is_reply is False


def test_parent_id_of_annotation():
    ann = Annotation()

    assert ann.parent_id is None


def test_thread_root_id_returns_id_if_no_references():
    annotation = Annotation(id="GBhy1DoHEea6htPothzqZQ")

    assert annotation.thread_root_id == "GBhy1DoHEea6htPothzqZQ"


def test_thread_root_id_returns_id_if_references_empty():
    annotation = Annotation(id="jANlljoHEea6hsv8FY7ipw", references=[])

    assert annotation.thread_root_id == "jANlljoHEea6hsv8FY7ipw"


def test_thread_root_id_returns_reference_if_only_one_reference():
    annotation = Annotation(
        id="qvJnIjoHEea6hiv0nJK7gw", references=["yiSVIDoHEea6hjcSFuROLw"]
    )

    assert annotation.thread_root_id == "yiSVIDoHEea6hjcSFuROLw"


def test_thread_root_id_returns_first_reference_if_many_references():
    annotation = Annotation(
        id="uK9yVjoHEea6hsewWuiKtQ",
        references=[
            "1Ife3DoHEea6hpv8vWujdQ",
            "uVuItjoHEea6hiNgv1wvmg",
            "Qe7fpc5ZRgWy0RSHEP9UNg",
        ],
    )

    assert annotation.thread_root_id == "1Ife3DoHEea6hpv8vWujdQ"


def test_text_setter_renders_markdown(markdown):
    markdown.render.return_value = "<p>foobar</p>"

    annotation = Annotation()
    annotation.text = "foobar"

    markdown.render.assert_called_once_with("foobar")

    annotation.text_rendered == markdown.render.return_value


@pytest.mark.parametrize(
    "userid,authority",
    [
        ("acct:bmason@hypothes.is", "hypothes.is"),
        ("acct:kaylawatson@elifesciences.org", "elifesciences.org"),
    ],
)
def test_authority(factories, userid, authority):
    assert factories.Annotation(userid=userid).authority == authority


def test_authority_when_annotation_has_no_userid():
    assert Annotation().authority is None


def test_setting_extras_inline_is_persisted(db_session, factories):
    """
    In-place changes to Annotation.extra should be persisted.

    Setting an Annotation.extra value in-place:

        my_annotation.extra['foo'] = 'bar'

    should be persisted to the database.

    """
    annotation = factories.Annotation(userid="fred")

    annotation.extra["foo"] = "bar"

    # We need to commit the db session here so that the in-place change to
    # annotation.extra above would be lost if annotation.extra was a normal
    # dict. Without this commit() this test would never fail.
    db_session.commit()

    annotation = db_session.query(Annotation).get(annotation.id)

    assert annotation.extra == {"foo": "bar"}


def test_deleting_extras_inline_is_persisted(db_session, factories):
    """
    In-place changes to Annotation.extra should be persisted.

    Deleting an Annotation.extra value in-place should be persisted to the
    database.

    """
    annotation = factories.Annotation(userid="fred", extra={"foo": "bar"})

    del annotation.extra["foo"]
    db_session.commit()
    annotation = db_session.query(Annotation).get(annotation.id)

    assert "foo" not in annotation.extra


def test_appending_tags_inline_is_persisted(db_session, factories):
    """
    In-place changes to Annotation.tags should be persisted.

    Changes made by Annotation.tags.append() should be persisted to the
    database.

    """
    annotation = factories.Annotation(userid="fred", tags=["foo"])

    annotation.tags.append("bar")
    db_session.commit()
    annotation = db_session.query(Annotation).get(annotation.id)

    assert "bar" in annotation.tags


def test_deleting_tags_inline_is_persisted(db_session, factories):
    """In-place deletions of annotation tags should be persisted."""
    annotation = factories.Annotation(userid="fred", tags=["foo"])

    del annotation.tags[0]
    db_session.commit()
    annotation = db_session.query(Annotation).get(annotation.id)

    assert "foo" not in annotation.tags


class TestThread(object):
    def test_empty_thread(self, root):
        assert root.thread == []

    def test_empty_thread_ids(self, root):
        assert root.thread_ids == []

    def test_thread_with_replies(self, root, reply, subreply):
        assert set(root.thread) == set([reply, subreply])

    def test_thread_ids_with_replies(self, root, reply, subreply):
        assert set(root.thread_ids) == set([reply.id, subreply.id])

    @pytest.mark.usefixtures("subreply")
    def test_reply_has_no_thread(self, reply):
        assert reply.thread == []

    @pytest.mark.usefixtures("subreply")
    def test_reply_has_no_thread_ids(self, reply):
        assert reply.thread_ids == []

    @pytest.fixture
    def root(self, factories):
        return factories.Annotation()

    @pytest.fixture
    def reply(self, factories, root):
        return factories.Annotation(references=[root.id])

    @pytest.fixture
    def subreply(self, factories, root, reply):
        return factories.Annotation(references=[root.id, reply.id])


@pytest.fixture
def markdown(patch):
    return patch("h.models.annotation.markdown")
