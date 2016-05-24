# -*- coding: utf-8 -*-
import mock

from h.nipsa import worker


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


@mock.patch("h.nipsa.worker.helpers", autospec=True)
def test_bulk_update_annotations_scans_with_query(helpers):
    client = mock.Mock(spec_set=['conn', 'index'])

    worker.bulk_update_annotations(client=client,
                                   query=mock.sentinel.query,
                                   action=mock.sentinel.action)

    helpers.scan.assert_called_once_with(client=client.conn,
                                         index=client.index,
                                         query=mock.sentinel.query)


@mock.patch("h.nipsa.worker.helpers", autospec=True)
def test_bulk_update_annotations_generates_actions_for_each_annotation(helpers):
    action = mock.Mock(spec_set=[])
    client = mock.Mock(spec_set=['conn', 'index'])
    helpers.scan.return_value = [mock.sentinel.anno1,
                                 mock.sentinel.anno2,
                                 mock.sentinel.anno3]

    worker.bulk_update_annotations(client=client,
                                   query=mock.sentinel.query,
                                   action=action)

    assert action.call_args_list == [
        mock.call(client.index, mock.sentinel.anno1),
        mock.call(client.index, mock.sentinel.anno2),
        mock.call(client.index, mock.sentinel.anno3),
    ]


@mock.patch("h.nipsa.worker.helpers", autospec=True)
def test_bulk_update_annotations_calls_bulk_with_actions(helpers):
    action = mock.Mock(spec_set=[], side_effect=[
        mock.sentinel.action1,
        mock.sentinel.action2,
        mock.sentinel.action3,
    ])
    client = mock.Mock(spec_set=['conn', 'index'])
    helpers.scan.return_value = [mock.sentinel.anno1,
                                 mock.sentinel.anno2,
                                 mock.sentinel.anno3]

    worker.bulk_update_annotations(client=client,
                                   query=mock.sentinel.query,
                                   action=action)

    helpers.bulk.assert_called_once_with(client=client.conn,
                                         actions=[mock.sentinel.action1,
                                                  mock.sentinel.action2,
                                                  mock.sentinel.action3])


@mock.patch("h.nipsa.worker.bulk_update_annotations", autospec=True)
@mock.patch("h.nipsa.worker.celery", autospec=True)
@mock.patch("h.nipsa.worker.search", autospec=True)
class TestAddNipsa(object):
    def test_calls_bulk_update_annotations(self, search, celery, bulk):
        celery.request = mock.Mock(spec_set=['feature', 'es'])
        celery.request.feature.return_value = True
        expected_query = search.not_nipsad_annotations('acct:jeannie@example.com')

        worker.add_nipsa('acct:jeannie@example.com')

        bulk.assert_any_call(celery.request.es,
                             expected_query,
                             worker.add_nipsa_action)


@mock.patch("h.nipsa.worker.bulk_update_annotations", autospec=True)
@mock.patch("h.nipsa.worker.celery", autospec=True)
@mock.patch("h.nipsa.worker.search", autospec=True)
class TestRemoveNipsa(object):
    def test_remove_nipsa_calls_bulk_update_annotations(self, search, celery, bulk):
        celery.request = mock.Mock(spec_set=['feature', 'es'])
        celery.request.feature.return_value = True
        expected_query = search.nipsad_annotations('acct:jeannie@example.com')

        worker.remove_nipsa('acct:jeannie@example.com')

        bulk.assert_any_call(celery.request.es,
                             expected_query,
                             worker.remove_nipsa_action)
