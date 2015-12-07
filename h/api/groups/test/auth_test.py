# -*- coding: utf-8 -*-
import copy
import mock

from h.api.groups import auth


def _mock_group(pubid):
    return mock.Mock(pubid=pubid)


def test_set_permissions_does_not_modify_annotations_with_no_permissions():
    annotations = [{
        'user': 'acct:jack@hypothes.is',
    },
    {
        'user': 'acct:jack@hypothes.is',
        'group': 'xyzabc',
    }]

    for ann in annotations:
        before = copy.deepcopy(ann)
        auth.set_permissions(ann)

        assert ann == before


def test_set_permissions_does_not_modify_private_annotations():
    original_annotation = {
        'user': 'acct:jack@hypothes.is',
        'group': 'xyzabc',
        'permissions': {
            'read': ['acct:jack@hypothes.is']
        }
    }
    annotation_to_be_modified = copy.deepcopy(original_annotation)


    auth.set_permissions(annotation_to_be_modified)

    assert annotation_to_be_modified == original_annotation


def test_set_permissions_does_not_modify_non_group_annotations():
    original_annotation = {
        'user': 'acct:jack@hypothes.is',
        'permissions': {
            'read': ['acct:jill@hypothes.is']
        },
        'group': '__world__'
    }
    annotation_to_be_modified = copy.deepcopy(original_annotation)

    auth.set_permissions(annotation_to_be_modified)

    assert annotation_to_be_modified == original_annotation


def test_set_permissions_sets_read_permissions_for_group_annotations():
    annotation = {
        'user': 'acct:jack@hypothes.is',
        'group': 'xyzabc',
        'permissions': {
            'read': ['group:__world__']
        }
    }

    auth.set_permissions(annotation)

    assert annotation['permissions']['read'] == ['group:xyzabc']


def test_group_principals_with_no_groups():
    user = mock.Mock(groups=[])

    assert auth.group_principals(user) == []


def test_group_principals_with_one_group():
    user = mock.Mock(groups=[_mock_group('pubid1')])

    assert auth.group_principals(user) == ['group:pubid1']


def test_group_principals_with_three_groups():
    user = mock.Mock(groups=[
        _mock_group('pubid1'),
        _mock_group('pubid2'),
        _mock_group('pubid3'),
    ])

    assert auth.group_principals(user) == [
        'group:pubid1',
        'group:pubid2',
        'group:pubid3',
    ]
