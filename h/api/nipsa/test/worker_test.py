import mock

from h.api.nipsa import worker


def test_add_nipsa_action():
    action = worker.add_nipsa_action("foo", {"_id": "test_id"})

    assert action == {
        "_op_type": "update",
        "_index": "foo",
        "_type": "annotation",
        "_id": "test_id",
        "doc": {"nipsa": True}
    }


def test_remove_nipsa_action():
    annotation = {"_id": "test_id", "_source": {"nipsa": True, "foo": "bar"}}
    action = worker.remove_nipsa_action("bar", annotation)

    assert action == {
        "_op_type": "index",
        "_index": "bar",
        "_type": "annotation",
        "_id": "test_id",
        "_source": {"foo": "bar"},
    }


@mock.patch("h.api.nipsa.worker.helpers")
@mock.patch("h.api.nipsa.worker.nipsa_search")
def test_add_nipsa_gets_query(nipsa_search, _):
    worker.add_or_remove_nipsa(client=mock.Mock(),
                               index="foo",
                               userid="test_userid",
                               action="add_nipsa")


    nipsa_search.not_nipsad_annotations.assert_called_once_with("test_userid")


@mock.patch("h.api.nipsa.worker.helpers")
@mock.patch("h.api.nipsa.worker.nipsa_search")
def test_remove_nipsa_gets_query(nipsa_search, _):
    worker.add_or_remove_nipsa(client=mock.Mock(),
                               index="foo",
                               userid="test_userid",
                               action="remove_nipsa")

    nipsa_search.nipsad_annotations.assert_called_once_with("test_userid")


@mock.patch("h.api.nipsa.worker.helpers")
@mock.patch("h.api.nipsa.worker.nipsa_search")
def test_add_nipsa_passes_es_client_to_scan(_, helpers):
    client = mock.Mock()

    worker.add_or_remove_nipsa(client=client,
                               index="foo",
                               userid="test_userid",
                               action="add_nipsa")

    assert helpers.scan.call_args[1]["client"] == client


@mock.patch("h.api.nipsa.worker.helpers")
@mock.patch("h.api.nipsa.worker.nipsa_search")
def test_remove_nipsa_passes_es_client_to_scan(_, helpers):
    client = mock.Mock()

    worker.add_or_remove_nipsa(client=client,
                               index="foo",
                               userid="test_userid",
                               action="remove_nipsa")

    assert helpers.scan.call_args[1]["client"] == client


@mock.patch("h.api.nipsa.worker.helpers")
@mock.patch("h.api.nipsa.worker.nipsa_search")
def test_add_nipsa_passes_query_to_scan(nipsa_search, helpers):
    query = mock.MagicMock()
    nipsa_search.not_nipsad_annotations.return_value = query

    worker.add_or_remove_nipsa(client=mock.Mock(),
                               index="foo",
                               userid="test_userid",
                               action="add_nipsa")

    assert helpers.scan.call_args[1]["query"] == query


@mock.patch("h.api.nipsa.worker.helpers")
@mock.patch("h.api.nipsa.worker.nipsa_search")
def test_remove_nipsa_passes_query_to_scan(nipsa_search, helpers):
    query = mock.MagicMock()
    nipsa_search.nipsad_annotations.return_value = query

    worker.add_or_remove_nipsa(client=mock.Mock(),
                               index="foo",
                               userid="test_userid",
                               action="remove_nipsa")

    assert helpers.scan.call_args[1]["query"] == query


@mock.patch("h.api.nipsa.worker.helpers")
@mock.patch("h.api.nipsa.worker.nipsa_search")
def test_add_nipsa_passes_actions_to_bulk(_, helpers):
    helpers.scan.return_value = [
        {"_id": "foo"}, {"_id": "bar"}, {"_id": "gar"}]

    worker.add_or_remove_nipsa(client=mock.Mock(),
                               index="foo",
                               userid="test_userid",
                               action="add_nipsa")

    actions = helpers.bulk.call_args[1]["actions"]
    assert [action["_id"] for action in actions] == ["foo", "bar", "gar"]


@mock.patch("h.api.nipsa.worker.helpers")
@mock.patch("h.api.nipsa.worker.nipsa_search")
def test_remove_nipsa_passes_actions_to_bulk(_, helpers):
    helpers.scan.return_value = [
        {"_id": "foo"}, {"_id": "bar"}, {"_id": "gar"}]

    worker.add_or_remove_nipsa(client=mock.Mock(),
                               index="foo",
                               userid="test_userid",
                               action="remove_nipsa")

    actions = helpers.bulk.call_args[1]["actions"]
    assert [action["_id"] for action in actions] == ["foo", "bar", "gar"]


@mock.patch("h.api.nipsa.worker.helpers")
@mock.patch("h.api.nipsa.worker.nipsa_search")
def test_add_nipsa_passes_es_client_to_bulk(_, helpers):
    client = mock.Mock()

    worker.add_or_remove_nipsa(client=client,
                               index="foo",
                               userid="test_userid",
                               action="remove_nipsa")

    assert helpers.bulk.call_args[1]["client"] == client


@mock.patch("h.api.nipsa.worker.helpers")
@mock.patch("h.api.nipsa.worker.nipsa_search")
def test_remove_nipsa_passes_actions_to_bulk(_, helpers):
    client = mock.Mock()

    worker.add_or_remove_nipsa(client=client,
                               index="foo",
                               userid="test_userid",
                               action="remove_nipsa")

    assert helpers.bulk.call_args[1]["client"] == client
