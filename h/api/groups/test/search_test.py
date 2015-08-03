import mock

from h.api.groups import search


def test_group_filter_with_0_groups():
    request = mock.Mock(effective_principals=['foo', 'bar'])

    group_filter = search.group_filter(request)

    assert group_filter == {'missing': {'field': 'group'}}


def test_group_filter_with_1_group():
    request = mock.Mock(effective_principals=['foo', 'bar', 'group:testgroup'])

    group_filter = search.group_filter(request)

    assert group_filter == {
        'bool': {
            'should': [
                {'missing': {'field': 'group'}},
                {'term': {'group': 'testgroup'}}
            ]
        }
    }


def test_group_filter_with_3_groups():
    request = mock.Mock(
            effective_principals=['foo', 'bar', 'group:testgroup',
                'group:my-group', 'group:another-group'])

    group_filter = search.group_filter(request)

    assert group_filter == {
        'bool': {
            'should': [
                {'missing': {'field': 'group'}},
                {
                    'terms': {
                        'group': ['testgroup', 'my-group', 'another-group']
                    }
                }
            ]
        }
    }
