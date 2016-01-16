# -*- coding: utf-8 -*-

import pytest

from sqlalchemy.dialects.postgresql import dialect

from h.api.db import types

FIXTURES = [
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

FIXTURES_INVALID = [
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


@pytest.mark.parametrize('app,db', FIXTURES)
def test_serialize(app, db):
    t = types.URLSafeUUID()
    assert t.process_bind_param(app, dialect) == db


@pytest.mark.parametrize('data', FIXTURES_INVALID)
def test_serialize_non_base64_data(data):
    t = types.URLSafeUUID()
    with pytest.raises(types.InvalidUUID):
        t.process_bind_param(data, dialect)


@pytest.mark.parametrize('app,db', FIXTURES)
def test_deserialize(app, db):
    t = types.URLSafeUUID()
    assert t.process_result_value(db, dialect) == app
