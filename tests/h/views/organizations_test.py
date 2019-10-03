# -*- coding: utf-8 -*-

from unittest import mock

from h.views import organizations


class TestOrganizationLogo:
    def test_it_returns_the_given_logo_unmodified(self):
        logo = organizations.organization_logo(
            mock.sentinel.logo, mock.sentinel.request
        )

        assert logo == mock.sentinel.logo
