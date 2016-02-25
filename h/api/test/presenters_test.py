# -*- coding: utf-8 -*-

import datetime
import mock

from h.api.presenters import DocumentURIJSONPresenter
from h.api.presenters import utc_iso8601, deep_merge_dict


class TestDocumentURIJSONPresenter(object):
    def test_asdict(self):
        docuri = mock.Mock(uri='http://example.com/site.pdf',
                           type='rel-alternate',
                           content_type='application/pdf')
        presenter = DocumentURIJSONPresenter(docuri)

        expected = {'href': 'http://example.com/site.pdf',
                    'rel': 'alternate',
                    'type': 'application/pdf'}

        assert expected == presenter.asdict()

    def test_asdict_empty_rel(self):
        docuri = mock.Mock(uri='http://example.com',
                           type='dc-doi',
                           content_type='text/html')
        presenter = DocumentURIJSONPresenter(docuri)

        expected = {'href': 'http://example.com', 'type': 'text/html'}

        assert expected == presenter.asdict()

    def test_asdict_empty_type(self):
        docuri = mock.Mock(uri='http://example.com',
                           type='rel-canonical',
                           content_type=None)
        presenter = DocumentURIJSONPresenter(docuri)

        expected = {'href': 'http://example.com', 'rel': 'canonical'}

        assert expected == presenter.asdict()

    def test_rel_with_type_rel(self):
        docuri = mock.Mock(type='rel-canonical')
        presenter = DocumentURIJSONPresenter(docuri)
        assert 'canonical' == presenter.rel

    def test_rel_with_non_rel_type(self):
        docuri = mock.Mock(type='highwire-pdf')
        presenter = DocumentURIJSONPresenter(docuri)
        assert presenter.rel is None

def test_utc_iso8601():
    t = datetime.datetime(2016, 2, 24, 18, 03, 25, 7685)
    assert utc_iso8601(t) == '2016-02-24T18:03:25.007685+00:00'


def test_utc_iso8601_ignores_timezone():
    t = datetime.datetime(2016, 2, 24, 18, 03, 25, 7685, Berlin())
    assert utc_iso8601(t) == '2016-02-24T18:03:25.007685+00:00'


def test_deep_merge_dict():
    a = {'foo': 1, 'bar': 2, 'baz': {'foo': 3, 'bar': 4}}
    b = {'bar': 8, 'baz': {'bar': 6, 'qux': 7}, 'qux': 15}
    deep_merge_dict(a, b)

    assert a == {
        'foo': 1,
        'bar': 8,
        'baz': {
            'foo': 3,
            'bar': 6,
            'qux': 7},
        'qux': 15}


class Berlin(datetime.tzinfo):
    """Berlin timezone, without DST support"""

    def utcoffset(self, dt):
        return datetime.timedelta(hours=1)

    def tzname(self, dt):
        return "Berlin"

    def dst(self, dt):
        return datetime.timedelta()
