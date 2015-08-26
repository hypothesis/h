# -*- coding: utf-8 -*-
import mock
import pytest

from h.api.search import transform


@pytest.mark.parametrize("ann_in,ann_out", [
    # Preserves the basics
    ({}, {}),
    ({"other": "keys", "left": "alone"}, {"other": "keys", "left": "alone"}),

    # Target field
    ({"target": "hello"}, {"target": "hello"}),
    ({"target": []}, {"target": []}),
    ({"target": ["foo", "bar"]}, {"target": ["foo", "bar"]}),
    ({"target": [{"foo": "bar"}, {"baz": "qux"}]},
     {"target": [{"foo": "bar"}, {"baz": "qux"}]}),
])
def test_prepare_noop_when_nothing_to_normalize(ann_in, ann_out):
    transform.prepare(ann_in)
    assert ann_in == ann_out


@pytest.mark.parametrize("ann_in,ann_out", [
    ({"target": [{"source": "giraffe"}]},
     {"target": [{"source": "giraffe", "source_normalized": "*giraffe*"}]}),
    ({"target": [{"source": "giraffe"}, "foo"]},
     {"target": [{"source": "giraffe", "source_normalized": "*giraffe*"},
                 "foo"]}),
])
def test_prepare_adds_source_normalized_field(ann_in, ann_out, uri_normalize):
    transform.prepare(ann_in)
    assert ann_in == ann_out


@pytest.mark.parametrize("ann_in,ann_out", [
    # Preserves the basics
    ({}, {}),
    ({"other": "keys", "left": "alone"}, {"other": "keys", "left": "alone"}),

    # Target field
    ({"target": "hello"}, {"target": "hello"}),
    ({"target": []}, {"target": []}),
    ({"target": ["foo", "bar"]}, {"target": ["foo", "bar"]}),
    ({"target": [{"foo": "bar"}, {"baz": "qux"}]},
     {"target": [{"foo": "bar"}, {"baz": "qux"}]}),
])
def test_render_noop_when_nothing_to_remove(ann_in, ann_out):
    assert transform.render(ann_in) == ann_out


@pytest.mark.parametrize("ann_in,ann_out", [
    ({"target": [{"source": "giraffe", "source_normalized": "*giraffe*"}]},
     {"target": [{"source": "giraffe"}]}),
    ({"target": [{"source": "giraffe", "source_normalized": "*giraffe*"},
                 "foo"]},
     {"target": [{"source": "giraffe"}, "foo"]}),
])
def test_render_removes_source_normalized_field(ann_in, ann_out):
    assert transform.render(ann_in) == ann_out


@pytest.fixture
def uri_normalize(request):
    patcher = mock.patch('h.api.uri.normalize', autospec=True)
    func = patcher.start()
    func.side_effect = lambda x: "*%s*" % x
    request.addfinalizer(patcher.stop)
    return func
