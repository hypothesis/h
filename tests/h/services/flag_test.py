# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.services import flag
from h import models
from h._compat import text_type, xrange


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


class TestFlagServiceCreate(object):
    def test_it_creates_flag(self, svc, db_session, factories):
        user = factories.User()
        annotation = factories.Annotation(userid=user.userid)

        svc.create(user, annotation)

        flag = db_session.query(models.Flag) \
                         .filter_by(user_id=user.id,
                                    annotation_id=annotation.id) \
                         .first()

        assert flag is not None

    def test_it_skips_creating_flag_when_already_exists(self, svc, db_session, factories):
        existing = factories.Flag()

        svc.create(existing.user, existing.annotation)

        assert db_session.query(models.Flag) \
                         .filter_by(user_id=existing.user.id,
                                    annotation_id=existing.annotation.id) \
                         .count() == 1


@pytest.mark.usefixtures('flags')
class TestFlagServiceList(object):
    def test_it_filters_by_user(self, svc, users, flags):
        expected = {f for k, f in flags.iteritems() if k.startswith('alice-')}
        assert set(svc.list(users['alice'])) == expected

    def test_it_optionally_filters_by_group(self, svc, users, flags, groups):
        expected = [flags['alice-politics']]
        result = svc.list(users['alice'], group=groups['politics']).all()
        assert result == expected

    def test_it_optionally_filters_by_uri(self, svc, users, flags):
        expected = [flags['alice-climate']]
        result = svc.list(users['alice'], uris=['https://science.org']).all()
        assert result == expected

    def test_it_supports_multiple_uri_filters(self, svc, users, flags):
        expected = [flags['alice-climate'], flags['alice-politics']]
        result = svc.list(users['alice'], uris=['https://science.org', 'https://news.com']).all()
        assert result == expected

    @pytest.fixture
    def users(self, factories):
        return {'alice': factories.User(username='alice'),
                'bob': factories.User(username='bob')}

    @pytest.fixture
    def groups(self, factories):
        return {'climate': text_type(factories.Group(name='Climate').pubid),
                'politics': text_type(factories.Group(name='Politics').pubid)}

    @pytest.fixture
    def flags(self, factories, users, groups, db_session):
        ann_climate = factories.Annotation(groupid=groups['climate'],
                                           target_uri='https://science.com')
        factories.DocumentURI(claimant='https://science.org',
                              uri='https://science.org',
                              type='rel-alternate',
                              document=ann_climate.document)

        ann_politics = factories.Annotation(groupid=groups['politics'],
                                            target_uri='https://news.com')

        return {
            'alice-climate': factories.Flag(user=users['alice'], annotation=ann_climate),
            'alice-politics': factories.Flag(user=users['alice'], annotation=ann_politics),
            'bob-politics': factories.Flag(user=users['bob'], annotation=ann_politics),
        }


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
