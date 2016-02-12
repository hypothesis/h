# -*- coding: utf-8 -*-

import copy

import mock
import pytest

from h.api import transform


def _fake_fetcher(ann):
    fetcher = mock.MagicMock()
    fetcher.return_value = ann
    return fetcher


def test_set_group_if_reply_does_not_modify_non_replies():
    fetcher = _fake_fetcher(None)
    # This annotation is not a reply.
    annotation = {'group': 'test-group'}

    transform.set_group_if_reply(annotation, fetcher=fetcher)

    assert annotation['group'] == 'test-group'


def test_set_group_if_reply_calls_fetcher_if_reply():
    fetcher = _fake_fetcher(None)
    annotation = {'references': ['parent_id']}

    transform.set_group_if_reply(annotation, fetcher=fetcher)

    fetcher.assert_called_once_with('parent_id')


def test_set_group_if_reply_does_nothing_if_parent_not_found():
    fetcher = _fake_fetcher(None)
    annotation = {'references': ['parent_id']}

    transform.set_group_if_reply(annotation, fetcher=fetcher)


def test_set_group_if_reply_adds_group_to_replies():
    """If a reply has no group it gets the group of its parent annotation."""
    fetcher = _fake_fetcher({'group': 'parent_group'})
    annotation = {'references': ['parent_id']}

    transform.set_group_if_reply(annotation, fetcher=fetcher)

    assert annotation['group'] == "parent_group"


def test_set_group_if_reply_overwrites_groups_in_replies():
    """If a reply has a group it's overwritten with the parent's group."""
    fetcher = _fake_fetcher({'group': 'parent_group'})
    annotation = {
        'group': 'this should be overwritten',
        'references': ['parent_id']
    }

    transform.set_group_if_reply(annotation, fetcher=fetcher)

    assert annotation['group'] == "parent_group"


def test_set_group_if_reply_clears_group_if_parent_has_no_group():
    fetcher = _fake_fetcher({})
    annotation = {
        'group': 'this should be deleted',
        'references': ['parent_id']
    }

    transform.set_group_if_reply(annotation, fetcher=fetcher)

    assert 'group' not in annotation


def test_insert_group_if_none_inserts_group():
    annotation = {}

    transform.insert_group_if_none(annotation)

    assert annotation == {'group': '__world__'}


def test_insert_group_if_none_does_not_overwrite_group():
    annotation = {'group': 'foo'}

    transform.insert_group_if_none(annotation)

    assert annotation == {'group': 'foo'}


def test_insert_group_if_none_does_nothing_if_already_group_world():
    annotation = {'group': '__world__'}

    transform.insert_group_if_none(annotation)

    assert annotation == {'group': '__world__'}


def test_set_group_permissions_does_not_modify_annotations_with_no_permissions():
    annotations = [{
        'user': 'acct:jack@hypothes.is',
    },
    {
        'user': 'acct:jack@hypothes.is',
        'group': 'xyzabc',
    }]

    for ann in annotations:
        before = copy.deepcopy(ann)
        transform.set_group_permissions(ann)

        assert ann == before


def test_set_group_permissions_does_not_modify_private_annotations():
    original_annotation = {
        'user': 'acct:jack@hypothes.is',
        'group': 'xyzabc',
        'permissions': {
            'read': ['acct:jack@hypothes.is']
        }
    }
    annotation_to_be_modified = copy.deepcopy(original_annotation)


    transform.set_group_permissions(annotation_to_be_modified)

    assert annotation_to_be_modified == original_annotation


def test_set_group_permissions_does_not_modify_non_group_annotations():
    original_annotation = {
        'user': 'acct:jack@hypothes.is',
        'permissions': {
            'read': ['acct:jill@hypothes.is']
        },
        'group': '__world__'
    }
    annotation_to_be_modified = copy.deepcopy(original_annotation)

    transform.set_group_permissions(annotation_to_be_modified)

    assert annotation_to_be_modified == original_annotation


def test_set_group_permissions_sets_read_permissions_for_group_annotations():
    annotation = {
        'user': 'acct:jack@hypothes.is',
        'group': 'xyzabc',
        'permissions': {
            'read': ['group:__world__']
        }
    }

    transform.set_group_permissions(annotation)

    assert annotation['permissions']['read'] == ['group:xyzabc']


@pytest.mark.usefixtures("uri_normalize")
@pytest.mark.parametrize("ann_in,ann_out", [
    # Adds scope field to annotations with target.source
    ({"target": [{"source": "giraffe"}]},
     {"target": [{"source": "giraffe", "scope": ["*giraffe*"]}]}),
    ({"target": [{"source": "giraffe"}, "foo"]},
     {"target": [{"source": "giraffe", "scope": ["*giraffe*"]},
                 "foo"]}),
])
def test_normalize_annotation_target_uris(ann_in, ann_out):
    transform.normalize_annotation_target_uris(ann_in)
    assert ann_in == ann_out


@pytest.mark.parametrize("ann_in,ann_out", [
    # Transforms annotations lacking target field (old-style comments)
    ({"uri": "giraffe"},
     {"uri": "giraffe", "target": [{"source": "giraffe"}]}),
    ({"uri": "giraffe", "target": []},
     {"uri": "giraffe", "target": [{"source": "giraffe"}]}),
    ({"uri": "giraffe", "references": None},
     {"uri": "giraffe",
      "references": None,
      "target": [{"source": "giraffe"}]}),
    ({"uri": "giraffe", "target": None},
     {"uri": "giraffe",
      "target": [{"source": "giraffe"}]}),
    ({"uri": "giraffe", "references": []},
     {"uri": "giraffe",
      "references": [],
      "target": [{"source": "giraffe"}]}),
    ({"uri": "giraffe", "references": [], "target": []},
     {"uri": "giraffe",
      "references": [],
      "target": [{"source": "giraffe"}]}),

    # Does nothing if either references or target is non-empty
    ({"uri": "giraffe", "references": ['hello'], "target": []},
     {"uri": "giraffe", "references": ['hello'], "target": []}),
    ({"uri": "giraffe", "references": [], "target": [{'foo': 'bar'}]},
     {"uri": "giraffe", "references": [], "target": [{'foo': 'bar'}]}),

    # Does nothing when lacking a uri
    ({"references": [], "target": []},
     {"references": [], "target": []}),
])
def test_fix_old_style_comments(ann_in, ann_out):
    transform.fix_old_style_comments(ann_in)
    assert ann_in == ann_out


@pytest.mark.parametrize("ann,nipsa", [
    ({"user": "george"}, True),
    ({"user": "georgia"}, False),
    ({}, False),
])
def test_add_nipsa(ann, nipsa, has_nipsa):
    has_nipsa.return_value = nipsa
    transform.add_nipsa(ann)
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
