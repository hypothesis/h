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


def test_render_unicode_csv():
    renderer = renderers.CSV({})
    req = DummyRequest()
    sys = {'request': req}
    value = {'header': [u'ӓ', u'č'],
             'rows': [[u'ñ', u'あ'], [u'ﺕ', u'Ӫ']]}

    assert renderer(value, sys) == u"ӓ,č\r\nñ,あ\r\nﺕ,Ӫ\r\n".encode('utf-8')
