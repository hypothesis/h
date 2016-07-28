# -*- coding: utf-8 -*-

import mock
import pytest

from sqlalchemy.dialects.postgresql import dialect

from memex.db import types

UUID_FIXTURES = [
    # 16 byte UUIDv4s
    ('OHFscuRvTmiwpOHWfrbzxw', '38716c72e46f4e68b0a4e1d67eb6f3c7'),
    ('JCfVA8bARx6wdjQq-vp9VA', '2427d503c6c0471eb076342afafa7d54'),
    ('3AlOaWxzQBKYjRtK3_Uyvw', 'dc094e696c734012988d1b4adff532bf'),

    # 15-byte ElasticSearch flake IDs
    ('AVGwR1YD8sFu_DXLVRKw',   '0151b0475603ef2c516efc35cb5512b0'),
    ('AVGy6_TM8sFu_DXLVRfp',   '0151b2ebf4ccef2c516efc35cb5517e9'),
    ('AVGM9RGq8sFu_DXLVN2l',   '01518cf511aaef2c516efc35cb54dda5'),

    # Null values
    (None, None),
]

UUID_FIXTURES_INVALID = [
    # Incorrect type
    123,
    [1, 2, 3],
    # 20 bytes of not-base64-encoded data
    '!!!@@@^abcdef&@@@!!!',
    # 22 bytes of not-base64-encoded data
    '!!!@@@^^abcdef&&@@@!!!',
    # short data
    'MDEyMzQ1Njc4OTAxMjM=',
    'MDEyMzQ1Njc4OTAxMjM0==',
    # long data
    'MDEyMzQ1Njc4OTAxMjM0NTY=',
    'YWxsIGtpbmRzIG9mIHdlaXJkIHN0dWZmIGdvaW5nIG9u',
]


@pytest.mark.parametrize('app,db', UUID_FIXTURES)
def test_uuid_serialize(app, db):
    t = types.URLSafeUUID()
    assert t.process_bind_param(app, dialect) == db


@pytest.mark.parametrize('data', UUID_FIXTURES_INVALID)
def test_uuid_serialize_non_base64_data(data):
    t = types.URLSafeUUID()
    with pytest.raises(types.InvalidUUID):
        t.process_bind_param(data, dialect)


@pytest.mark.parametrize('app,db', UUID_FIXTURES)
def test_uuid_deserialize(app, db):
    t = types.URLSafeUUID()
    assert t.process_result_value(db, dialect) == app


def test_annotation_selector_serialize():
    t = types.AnnotationSelectorJSONB()
    selectors = [{
        'type': 'TextQuoteSelector',
        'prefix': u'\u0000Lorem ipsum ',
        'exact': u'dolor sit amet,\u0000 ',
        'suffix': u'consectetur\u0000 adipiscing elit.'
    }]

    value = t.process_bind_param(selectors, dialect)
    assert value[0]['prefix'] == u'\\u0000Lorem ipsum '
    assert value[0]['exact'] == 'dolor sit amet,\\u0000 '
    assert value[0]['suffix'] == 'consectetur\\u0000 adipiscing elit.'


def test_annotation_selector_serialize_missing_text_quote_selector():
    t = types.AnnotationSelectorJSONB()
    selectors = [{
        'type': 'RangeSelector',
        'startContainer': '/div[1]/div[2]',
        'endContainer': '/div[1]/div[3]',
        'startOffset': 39,
        'endoffset': 1
    }]
    assert t.process_bind_param(selectors, dialect) == selectors


def test_annotation_selector_deserialize():
    t = types.AnnotationSelectorJSONB()
    selectors = [{
        'type': 'TextQuoteSelector',
        'prefix': u'\\u0000Lorem ipsum ',
        'exact': u'dolor sit amet,\\u0000 ',
        'suffix': u'consectetur\\u0000 adipiscing elit.'
    }]

    value = t.process_result_value(selectors, dialect)
    assert value[0]['prefix'] == u'\u0000Lorem ipsum '
    assert value[0]['exact'] == u'dolor sit amet,\u0000 '
    assert value[0]['suffix'] == u'consectetur\u0000 adipiscing elit.'


def test_annotation_selector_deserialize_missing_text_quote_selector():
    t = types.AnnotationSelectorJSONB()
    selectors = [{
        'type': 'RangeSelector',
        'startContainer': '/div[1]/div[2]',
        'endContainer': '/div[1]/div[3]',
        'startOffset': 39,
        'endoffset': 1
    }]
    assert t.process_result_value(selectors, dialect) == selectors


class TestMutableList(object):

    @mock.patch.object(types.Mutable, 'changed')
    @pytest.mark.parametrize('operation', [
        lambda l: l.__setitem__(0, 'value'),
        lambda l: l.__setslice__(1, 3, ['a', 'b']),
        lambda l: l.__delitem__(0),
        lambda l: l.__delslice__(1, 3),
        lambda l: l.append('value'),
        lambda l: l.insert(0, 'value'),
        lambda l: l.extend(['value']),
        lambda l: l.pop(),
        lambda l: l.remove(1),
        lambda l: l.sort(),
        lambda l: l.reverse(),
    ])
    def test_it_calls_changed(self, changed, operation):
        list_ = types.MutableList([1, 2, 3])
        assert not changed.called

        operation(list_)

        changed.assert_called_once_with()

    @pytest.mark.parametrize('operation,expected_result', [
        (lambda l: l.__setitem__(0, 'value'), ['value', 3, 2]),
        (lambda l: l.__setslice__(1, 3, ['a', 'b']), [1, 'a', 'b']),
        (lambda l: l.__delitem__(0), [3, 2]),
        (lambda l: l.__delslice__(1, 3), [1]),
        (lambda l: l.append('value'), [1, 3, 2, 'value']),
        (lambda l: l.insert(0, 'value'), ['value', 1, 3, 2]),
        (lambda l: l.extend(['value']), [1, 3, 2, 'value']),
        (lambda l: l.pop(), [1, 3]),
        (lambda l: l.remove(1), [3, 2]),
        (lambda l: l.sort(), [1, 2, 3]),
        (lambda l: l.reverse(), [2, 3, 1]),
    ])
    def test_it_mutates_the_list(self, operation, expected_result):
        list_ = types.MutableList([1, 3, 2])

        operation(list_)

        assert list_ == expected_result

    def test_pop_returns_the_popped_value(self):
        assert types.MutableList(['value']).pop() == 'value'
