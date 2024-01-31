import pytest

from h.services.nipsa import NipsaService, nipsa_factory


class TestNipsaService:
    def test_fetch_all_flagged_userids_returns_set_of_userids(self, svc):
        assert svc.fetch_all_flagged_userids() == {
            "acct:flagged_user@example.com",
            "acct:flagged_user_2@example.com",
        }

    def test_is_flagged_returns_true_for_flagged_users(self, svc):
        assert svc.is_flagged("acct:flagged_user@example.com")

    def test_is_flagged_returns_false_for_unflagged_users(self, svc):
        assert not svc.is_flagged("acct:unflagged_user@example.com")

    def test_is_flagged_returns_false_for_unknown_users(self, svc):
        assert not svc.is_flagged("acct:not_in_the_db@example.com")

    def test_flag_sets_nipsa_true(self, svc, users):
        svc.flag(users["unflagged_user"])

        assert svc.is_flagged("acct:unflagged_user@example.com")
        assert users["unflagged_user"].nipsa is True

    def test_flag_triggers_reindex_job(self, svc, users, tasks):
        svc.flag(users["unflagged_user"])

        tasks.job_queue.add_annotations_from_user.delay.assert_called_once_with(
            "sync_annotation",
            "acct:unflagged_user@example.com",
            tag="NipsaService.flag",
            force=True,
            schedule_in=30,
        )

    def test_unflag_sets_nipsa_false(self, svc, users):
        svc.unflag(users["flagged_user"])

        assert not svc.is_flagged("acct:flagged_user@example.com")
        assert not users["flagged_user"].nipsa

    def test_unflag_triggers_reindex_job(self, svc, users, tasks):
        svc.unflag(users["flagged_user"])

        tasks.job_queue.add_annotations_from_user.delay.assert_called_once_with(
            "sync_annotation",
            "acct:flagged_user@example.com",
            tag="NipsaService.unflag",
            force=True,
            schedule_in=30,
        )

    def test_fetch_all_flagged_userids_caches_lookup(self, svc, users):
        svc.fetch_all_flagged_userids()
        users["flagged_user"].nipsa = False

        # Returns `True` because status is cached.
        assert svc.is_flagged("acct:flagged_user@example.com")
        assert svc.fetch_all_flagged_userids() == {
            "acct:flagged_user@example.com",
            "acct:flagged_user_2@example.com",
        }

    def test_flag_updates_cache(self, svc, users):
        svc.fetch_all_flagged_userids()
        svc.flag(users["unflagged_user"])
        users["unflagged_user"].nipsa = (
            False  # Make sure result below comes from cache.
        )

        assert svc.is_flagged(users["unflagged_user"].userid)

    def test_unflag_updates_cache(self, svc, users):
        svc.fetch_all_flagged_userids()
        svc.unflag(users["flagged_user"])
        users["flagged_user"].nipsa = True  # Make sure result below comes from cache.

        assert not svc.is_flagged(users["flagged_user"].userid)

    def test_clear_resets_cache(self, svc, users):
        svc.fetch_all_flagged_userids()
        users["flagged_user"].nipsa = False
        svc.clear()

        assert not svc.is_flagged("acct:flagged_user@example.com")

    @pytest.fixture
    def svc(self, db_session):
        return NipsaService(db_session)

    @pytest.fixture(autouse=True)
    def tasks(self, patch):
        return patch("h.services.nipsa.tasks")

    @pytest.fixture(autouse=True)
    def users(self, db_session, factories):
        users = {
            "flagged_user": factories.User(username="flagged_user", nipsa=True),
            "flagged_user_2": factories.User(username="flagged_user_2", nipsa=True),
            "unflagged_user": factories.User(username="unflagged_user", nipsa=False),
        }
        db_session.flush()
        return users


def test_nipsa_factory(pyramid_request):
    svc = nipsa_factory(None, pyramid_request)

    assert isinstance(svc, NipsaService)
    assert svc.session == pyramid_request.db
