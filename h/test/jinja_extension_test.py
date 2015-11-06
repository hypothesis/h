# -*- coding: utf-8 -*-

import pytest

from h import jinja_extensions as ext


@pytest.mark.parametrize("value_in,json_out", [
  ({"foo": 42}, "{\"foo\": 42}")
])
def test_to_json(value_in, json_out):
    result = str(ext.to_json(value_in))

    assert result == json_out
