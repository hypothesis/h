# -*- coding: utf-8 -*-
from pyramid.testing import DummyRequest

from h import renderers


def test_response_content_type():
    renderer = renderers.CSV({})
    req = DummyRequest()
    renderer({}, {'request': req})
    assert req.response.content_type == 'text/csv'


def test_render_simple_csv():
    renderer = renderers.CSV({})
    req = DummyRequest()
    sys = {'request': req}
    value = {'header': ['One', 'Two'],
             'rows': [[1, 2], [3, 4]]}

    assert renderer(value, sys) == "One,Two\r\n1,2\r\n3,4\r\n"
