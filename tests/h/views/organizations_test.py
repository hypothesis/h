# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.views import organizations

import mock


class TestOrganizationLogo(object):
    def test_it_returns_the_given_logo_unmodified(self):
        logo = organizations.organization_logo(
            mock.sentinel.logo, mock.sentinel.request
        )

        assert logo == mock.sentinel.logo
