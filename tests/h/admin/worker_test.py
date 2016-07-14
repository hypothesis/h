# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.admin import worker


class TestRenameUser(object):
    def test_it_finds_the_service(self, celery):
        worker.rename_user(4, 'panda')

        celery.request.find_service.assert_called_once_with(name='rename_user')

    def test_it_renames_the_user(self, celery):
        service = celery.request.find_service.return_value

        worker.rename_user(4, 'panda')

        service.rename.assert_called_once_with(4, 'panda')

    @pytest.fixture
    def celery(self, patch, pyramid_request):
        return patch('h.admin.worker.celery', autospec=False)
