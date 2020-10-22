import pytest

from h.services.nipsa import NipsaService, nipsa_factory


class TestNipsaService:
    def test_fetch_all_flagged_userids_returns_set_of_userids(self, svc):
        assert svc.fetch_all_flagged_userids() == {
            "acct:renata@example.com",
            "acct:cecilia@example.com",
        }

    def test_is_flagged_returns_true_for_flagged_users(self, svc, users):
        assert svc.is_flagged("acct:renata@example.com")
        assert svc.is_flagged("acct:cecilia@example.com")

    def test_is_flagged_returns_false_for_unflagged_users(self, svc):
        assert not svc.is_flagged("acct:dominic@example.com")

    def test_is_flagged_returns_false_for_unknown_users(self, svc):
        assert not svc.is_flagged("acct:not_in_the_db@example.com")

    def test_flag_sets_nipsa_true(self, svc, users):
        svc.flag(users["dominic"])

        assert svc.is_flagged("acct:dominic@example.com")
        assert users["dominic"].nipsa is True

    def test_flag_triggers_reindex_job(self, svc, users, search_index):
        svc.flag(users["dominic"])

        search_index.add_users_annotations.assert_called_once_with(
            "acct:dominic@example.com",
            "NipsaService.flag",
            force=True,
            schedule_in=30,
        )

    def test_unflag_sets_nipsa_false(self, svc, users):
        svc.unflag(users["renata"])

        assert not svc.is_flagged("acct:renata@example.com")
        assert users["renata"].nipsa is False

    def test_unflag_triggers_reindex_job(self, svc, users, search_index):
        svc.unflag(users["renata"])

        search_index.add_users_annotations.assert_called_once_with(
            "acct:renata@example.com",
            "NipsaService.unflag",
            force=True,
            schedule_in=30,
        )

    def test_fetch_all_flagged_userids_caches_lookup(self, svc, users):
        svc.fetch_all_flagged_userids()
        users["renata"].nipsa = False

        # Returns `True` because status is cached.
        assert svc.is_flagged("acct:renata@example.com")
        assert svc.fetch_all_flagged_userids() == {
            "acct:renata@example.com",
            "acct:cecilia@example.com",
        }

    def test_flag_updates_cache(self, svc, users):
        svc.fetch_all_flagged_userids()
        svc.flag(users["dominic"])
        users["dominic"].nipsa = False  # Make sure result below comes from cache.

        assert svc.is_flagged(users["dominic"].userid)

    def test_unflag_updates_cache(self, svc, users):
        svc.fetch_all_flagged_userids()
        svc.unflag(users["renata"])
        users["renata"].nipsa = True  # Make sure result below comes from cache.

        assert not svc.is_flagged(users["renata"].userid)

    def test_clear_resets_cache(self, svc, users):
        svc.fetch_all_flagged_userids()
        users["renata"].nipsa = False
        svc.clear()

        assert not svc.is_flagged("acct:renata@example.com")

    @pytest.fixture
    def svc(self, db_session, search_index):
        return NipsaService(db_session, search_index)

    @pytest.fixture(autouse=True)
    def users(self, db_session, factories):
        users = {
            "renata": factories.User(username="renata", nipsa=True),
            "cecilia": factories.User(username="cecilia", nipsa=True),
            "dominic": factories.User(username="dominic", nipsa=False),
        }
        db_session.flush()
        return users


def test_nipsa_factory(pyramid_request, search_index):
    svc = nipsa_factory(None, pyramid_request)

    assert isinstance(svc, NipsaService)
    assert svc.session == pyramid_request.db
    assert svc._get_search_index() == search_index
