# -*- coding: utf-8 -*-


from h.views.admin_index import index


class TestIndex(object):
    def test_release_info(self, pyramid_request):
        result = index(pyramid_request)

        assert 'release_info' in result
        assert 'hostname' in result['release_info']
        assert 'python_version' in result['release_info']
        assert 'version' in result['release_info']
