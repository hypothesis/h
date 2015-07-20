import mock

from h.api.nipsa import worker


def test_add_nipsa_action():
    action = worker.add_nipsa_action({"_id": "test_id"})

    assert action == {
        "_op_type": "update",
        "_index": "annotator",
        "_type": "annotation",
        "_id": "test_id",
        "doc": {"not_in_public_site_areas": True}
    }


def test_remove_nipsa_action():
    action = worker.remove_nipsa_action({"_id": "test_id"})

    assert action == {
        "_op_type": "update",
        "_index": "annotator",
        "_type": "annotation",
        "_id": "test_id",
        "script": "ctx._source.remove(\"not_in_public_site_areas\")"
    }


@mock.patch("h.api.nipsa.worker.search")
@mock.patch("h.api.nipsa.worker.nipsa_search")
def test_add_nipsa_gets_query(nipsa_search, _):
    worker.add_or_remove_nipsa("test_user_id", "nipsa", mock.Mock())

    nipsa_search.not_nipsad_annotations.assert_called_once_with("test_user_id")


@mock.patch("h.api.nipsa.worker.search")
@mock.patch("h.api.nipsa.worker.nipsa_search")
def test_remove_nipsa_gets_query(nipsa_search, _):
    worker.add_or_remove_nipsa("test_user_id", "unnipsa", mock.Mock())

    nipsa_search.nipsad_annotations.assert_called_once_with("test_user_id")


@mock.patch("h.api.nipsa.worker.search")
@mock.patch("h.api.nipsa.worker.nipsa_search")
def test_add_nipsa_passes_es_client_to_scan(_, search):
    es_client = mock.Mock()

    worker.add_or_remove_nipsa("test_user_id", "nipsa", es_client)

    assert search.scan.call_args[1]["es_client"] == es_client


@mock.patch("h.api.nipsa.worker.search")
@mock.patch("h.api.nipsa.worker.nipsa_search")
def test_remove_nipsa_passes_es_client_to_scan(_, search):
    es_client = mock.Mock()

    worker.add_or_remove_nipsa("test_user_id", "unnipsa", es_client)

    assert search.scan.call_args[1]["es_client"] == es_client


@mock.patch("h.api.nipsa.worker.search")
@mock.patch("h.api.nipsa.worker.nipsa_search")
def test_add_nipsa_passes_query_to_scan(nipsa_search, search):
    query = mock.MagicMock()
    nipsa_search.not_nipsad_annotations.return_value = query

    worker.add_or_remove_nipsa("test_user_id", "nipsa", mock.Mock())

    assert search.scan.call_args[1]["query"] == query


@mock.patch("h.api.nipsa.worker.search")
@mock.patch("h.api.nipsa.worker.nipsa_search")
def test_remove_nipsa_passes_query_to_scan(nipsa_search, search):
    query = mock.MagicMock()
    nipsa_search.nipsad_annotations.return_value = query

    worker.add_or_remove_nipsa("test_user_id", "unnipsa", mock.Mock())

    assert search.scan.call_args[1]["query"] == query


@mock.patch("h.api.nipsa.worker.search")
@mock.patch("h.api.nipsa.worker.nipsa_search")
def test_add_nipsa_passes_actions_to_bulk(_, search):
    search.scan.return_value = [
        {"_id": "foo"}, {"_id": "bar"}, {"_id": "gar"}]

    worker.add_or_remove_nipsa("test_user_id", "nipsa", mock.Mock())

    actions = search.bulk.call_args[1]["actions"]
    assert [action["_id"] for action in actions] == ["foo", "bar", "gar"]


@mock.patch("h.api.nipsa.worker.search")
@mock.patch("h.api.nipsa.worker.nipsa_search")
def test_remove_nipsa_passes_actions_to_bulk(_, search):
    search.scan.return_value = [
        {"_id": "foo"}, {"_id": "bar"}, {"_id": "gar"}]

    worker.add_or_remove_nipsa("test_user_id", "unnipsa", mock.Mock())

    actions = search.bulk.call_args[1]["actions"]
    assert [action["_id"] for action in actions] == ["foo", "bar", "gar"]


@mock.patch("h.api.nipsa.worker.search")
@mock.patch("h.api.nipsa.worker.nipsa_search")
def test_add_nipsa_passes_es_client_to_bulk(_, search):
    es_client = mock.Mock()

    worker.add_or_remove_nipsa("test_user_id", "nipsa", es_client)

    assert search.bulk.call_args[1]["es_client"] == es_client


@mock.patch("h.api.nipsa.worker.search")
@mock.patch("h.api.nipsa.worker.nipsa_search")
def test_remove_nipsa_passes_actions_to_bulk(_, search):
    es_client = mock.Mock()

    worker.add_or_remove_nipsa("test_user_id", "unnipsa", es_client)

    assert search.bulk.call_args[1]["es_client"] == es_client
