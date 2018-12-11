# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.services import flag
from h import models


@pytest.mark.usefixtures("flags")
class TestFlagServiceFlagged(object):
    def test_it_returns_true_when_flag_exists(self, svc, flags):
        user = flags[-1].user
        annotation = flags[-1].annotation

        assert svc.flagged(user, annotation) is True

    def test_it_returns_false_when_flag_does_not_exist(self, svc, factories):
        user = factories.User()
        annotation = factories.Annotation(userid=user.userid)

        assert svc.flagged(user, annotation) is False

    def test_it_lists_flagged_ids(self, svc, flags):
        user = flags[-1].user

        all_flagged = svc.all_flagged(user, [f.annotation_id for f in flags])

        assert all_flagged == set([flags[-1].annotation_id])

    @pytest.mark.usefixtures("flags")
    def test_it_handles_all_flagged_with_no_ids(self, svc, factories):
        user = factories.User()
        assert svc.all_flagged(user, []) == set()

    def test_it_handles_all_flagged_with_no_user(self, svc, flags):
        annotation_ids = [f.annotation_id for f in flags]

        assert svc.all_flagged(None, annotation_ids) == set()

    @pytest.fixture
    def flags(self, factories):
        return factories.Flag.create_batch(3)


class TestFlagServiceCreate(object):
    def test_it_creates_flag(self, svc, db_session, factories):
        user = factories.User()
        annotation = factories.Annotation(userid=user.userid)

        svc.create(user, annotation)

        flag = (
            db_session.query(models.Flag)
            .filter_by(user_id=user.id, annotation_id=annotation.id)
            .first()
        )

        assert flag is not None

    def test_it_skips_creating_flag_when_already_exists(
        self, svc, db_session, factories
    ):
        existing = factories.Flag()

        svc.create(existing.user, existing.annotation)

        assert (
            db_session.query(models.Flag)
            .filter_by(user_id=existing.user.id, annotation_id=existing.annotation.id)
            .count()
            == 1
        )


class TestFlagServiceFactory(object):
    def test_it_returns_flag_service(self, pyramid_request):
        svc = flag.flag_service_factory(None, pyramid_request)
        assert isinstance(svc, flag.FlagService)

    def test_it_provides_request_db_as_session(self, pyramid_request):
        svc = flag.flag_service_factory(None, pyramid_request)
        assert svc.session == pyramid_request.db


@pytest.fixture
def svc(db_session):
    return flag.FlagService(db_session)
