# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h import textutil


@pytest.mark.parametrize("text,slug", [
    ("foo", "foo"),
    ("Foo", "foo"),
    ("Foo Bar", "foo-bar"),
    ("Foo! Bar (Baz)", "foo-bar-baz"),
    ("Foo! Bar (Baz)", "foo-bar-baz"),
    ("Ἀλέξανδρος ὁ Μακεδών", "alexandros-o-makedon"),
    ("Лев Никола́евич Толсто́й", "lev-nikolaevich-tolstoi"),
    ("孔子", "kong-zi"),
])
def test_slugify(text, slug):
    assert textutil.slugify(text) == slug
