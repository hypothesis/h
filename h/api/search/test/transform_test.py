# -*- coding: utf-8 -*-
import mock
import pytest

from h.api.search import transform


@mock.patch('h.api.search.transform.groups')
def test_prepare_calls_set_group_if_reply(groups):
    annotation = {'permissions': {'read': []}}

    transform.prepare(annotation)

    groups.set_group_if_reply.assert_called_once_with(annotation)


@mock.patch('h.api.search.transform.groups')
def test_prepare_calls_insert_group(groups):
    annotation = {'permissions': {'read': []}}

    transform.prepare(annotation)

    groups.insert_group_if_none.assert_called_once_with(annotation)


@mock.patch('h.api.search.transform.groups')
def test_prepare_calls_set_permissions(groups):
    annotation = {'permissions': {'read': []}}

    transform.prepare(annotation)

    groups.set_permissions.assert_called_once_with(annotation)


@mock.patch('h.api.search.transform.groups')
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
def test_prepare_noop_when_nothing_to_normalize(_, ann_in, ann_out):
    transform.prepare(ann_in)
    assert ann_in == ann_out


@mock.patch('h.api.search.transform.groups')
@pytest.mark.parametrize("ann_in,ann_out", [
    ({"target": [{"source": "giraffe"}]},
     {"target": [{"source": "giraffe", "scope": ["*giraffe*"]}]}),
    ({"target": [{"source": "giraffe"}, "foo"]},
     {"target": [{"source": "giraffe", "scope": ["*giraffe*"]},
                 "foo"]}),
])
def test_prepare_adds_scope_field(_, ann_in, ann_out, uri_normalize):
    transform.prepare(ann_in)
    assert ann_in == ann_out


@mock.patch('h.api.search.transform.groups')
@pytest.mark.usefixtures("uri_normalize")
@pytest.mark.parametrize("ann_in,ann_out", [
    ({"uri": "giraffe"},
     {"uri": "giraffe",
      "target": [{"source": "giraffe", "scope": ["*giraffe*"]}]}),
    ({"uri": "giraffe", "target": []},
     {"uri": "giraffe",
      "target": [{"source": "giraffe", "scope": ["*giraffe*"]}]}),
    ({"uri": "giraffe", "references": None},
     {"uri": "giraffe",
      "references": None,
      "target": [{"source": "giraffe", "scope": ["*giraffe*"]}]}),
    ({"uri": "giraffe", "target": None},
     {"uri": "giraffe",
      "target": [{"source": "giraffe", "scope": ["*giraffe*"]}]}),
    ({"uri": "giraffe", "references": []},
     {"uri": "giraffe",
      "references": [],
      "target": [{"source": "giraffe", "scope": ["*giraffe*"]}]}),
    ({"uri": "giraffe", "references": [], "target": []},
     {"uri": "giraffe",
      "references": [],
      "target": [{"source": "giraffe", "scope": ["*giraffe*"]}]}),

    # Does nothing if either references or target is non-empty
    ({"uri": "giraffe", "references": ['hello'], "target": []},
     {"uri": "giraffe", "references": ['hello'], "target": []}),
    ({"uri": "giraffe", "references": [], "target": [{'foo': 'bar'}]},
     {"uri": "giraffe", "references": [], "target": [{'foo': 'bar'}]}),

    # Does nothing when lacking a uri
    ({"references": [], "target": []},
     {"references": [], "target": []}),
])
def test_prepare_transforms_old_style_comments(groups, ann_in, ann_out):
    transform.prepare(ann_in)
    assert ann_in == ann_out


@mock.patch('h.api.search.transform.groups')
@pytest.mark.parametrize("ann,nipsa", [
    ({"user": "george"}, True),
    ({"user": "georgia"}, False),
    ({}, False),
])
def test_prepare_sets_nipsa_field(_, ann, nipsa, has_nipsa):
    has_nipsa.return_value = nipsa
    transform.prepare(ann)
    if nipsa:
        assert ann["nipsa"] is True
    else:
        assert "nipsa" not in ann


@pytest.fixture
def has_nipsa(request):
    patcher = mock.patch('h.api.nipsa.has_nipsa', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def uri_normalize(request):
    patcher = mock.patch('h.api.uri.normalize', autospec=True)
    func = patcher.start()
    func.side_effect = lambda x: "*%s*" % x
    request.addfinalizer(patcher.stop)
    return func
