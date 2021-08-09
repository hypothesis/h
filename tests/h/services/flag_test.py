import pytest

from h import models
from h.services import flag


class TestFlagServiceFlagged:
    def test_it_returns_true_when_flag_exists(self, svc, flag):
        assert svc.flagged(flag.user, flag.annotation) is True

    def test_it_returns_false_when_flag_does_not_exist(self, svc, factories):
        user = factories.User()
        annotation = factories.Annotation(userid=user.userid)

        assert not svc.flagged(user, annotation)

    def test_it_lists_flagged_ids(self, svc, flag, noise):
        annotation_ids = [flag.annotation_id for flag in noise]
        annotation_ids.append(flag.annotation_id)

        all_flagged = svc.all_flagged(flag.user, annotation_ids)

        assert all_flagged == {flag.annotation_id}

    def test_it_handles_all_flagged_with_no_ids(self, svc, factories):
        user = factories.User()

        assert svc.all_flagged(user, []) == set()

    def test_it_handles_all_flagged_with_no_user(self, svc, flag):
        assert svc.all_flagged(None, [flag.annotation_id]) == set()

    @pytest.fixture
    def flag(self, factories):
        return factories.Flag()

    @pytest.fixture(autouse=True)
    def noise(self, factories):
        return factories.Flag.create_batch(2)


class TestFlagServiceCreate:
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


class TestFlagServiceCount:
    def test_flag_count_returns_zero_for_unflagged_annotation(self, svc, unflagged):
        assert not svc.flag_count(unflagged)

    def test_flag_count_returns_flag_count_for_flagged_annotation(self, svc, flagged):
        assert svc.flag_count(flagged) == 2

    def test_flag_counts_returns_empty_dict_for_no_ids(self, svc):
        assert svc.flag_counts([]) == {}

    def test_flag_counts_returns_all_ids_in_result(self, svc, flagged, unflagged):
        ann_ids = [flagged.id, unflagged.id]

        flag_counts = svc.flag_counts(ann_ids)

        assert set(flag_counts.keys()) == set(ann_ids)

    def test_flag_counts_returns_zero_for_unflagged_annotation(self, svc, unflagged):
        flag_counts = svc.flag_counts([unflagged.id])

        assert not flag_counts[unflagged.id]

    def test_flag_counts_returns_flag_count_for_flagged_annotation(self, svc, flagged):
        flag_counts = svc.flag_counts([flagged.id])

        assert flag_counts[flagged.id] == 2

    @pytest.fixture
    def unflagged(self, factories):
        return factories.Annotation()

    @pytest.fixture
    def flagged(self, factories):
        annotation = factories.Annotation()
        factories.Flag.create_batch(2, annotation=annotation)
        return annotation


class TestFlagServiceFactory:
    def test_it_returns_flag_service(self, pyramid_request):
        svc = flag.flag_service_factory(None, pyramid_request)
        assert isinstance(svc, flag.FlagService)


@pytest.fixture
def svc(db_session):
    return flag.FlagService(db_session)
