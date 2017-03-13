# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.services import flag
from h._compat import xrange


@pytest.mark.usefixtures('flags')
class TestFlagServiceFlagged(object):
    def test_it_returns_true_when_flag_exists(self, svc, flags):
        user = flags[-1].user
        annotation = flags[-1].annotation

        assert svc.flagged(user, annotation) is True

    def test_it_returns_false_when_flag_does_not_exist(self, svc, factories):
        user = factories.User()
        annotation = factories.Annotation(userid=user.userid)

        assert svc.flagged(user, annotation) is False

    @pytest.fixture
    def flags(self, factories):
        return [factories.Flag() for _ in xrange(3)]

    @pytest.fixture
    def svc(self, db_session):
        return flag.FlagService(db_session)


class TestFlagServiceFactory(object):
    def test_it_returns_flag_service(self, pyramid_request):
        svc = flag.flag_service_factory(None, pyramid_request)
        assert isinstance(svc, flag.FlagService)

    def test_it_provides_request_db_as_session(self, pyramid_request):
        svc = flag.flag_service_factory(None, pyramid_request)
        assert svc.session == pyramid_request.db
