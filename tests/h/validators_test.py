# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
from mock import Mock

import colander

from h.validators import Email


class TestEmail(object):
    @pytest.mark.parametrize('email', [
        'jimsmith@foobar.com',
        'international@xn--domain.com',
        'jim.smith@gmail.com',
        'jim.smith@foo.bar.com',
        'a.range!of#punctuation-chars$are+accepted@gmail.com',
    ])
    def test_accepts_valid_addresses(self, schema_node, email):
        validator = Email()
        validator(schema_node, email)

    @pytest.mark.parametrize('email', [
        ' spaces @ spaces.com',
        'sorry-ascii-only-🤠@gmail.com',
        'no-domain-part@',
        '@no-local-part.com',
        'no-at-separator',

        # A non-TLD part is required, but the TLD itself is optional.
        'local@.only-a-tld',
    ])
    def test_rejects_invalid_addresses(self, schema_node, email):
        validator = Email()

        with pytest.raises(colander.Invalid):
            validator(schema_node, email)

    @pytest.fixture
    def schema_node(self):
        """
        Mock for `colander.SchemaNode` arg that validator callables require.
        """
        return Mock(spec_set=[])
