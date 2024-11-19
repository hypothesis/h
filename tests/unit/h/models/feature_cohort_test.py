from h.models.feature_cohort import FeatureCohortUser


class TestFeatureCohortUser:
    def test_repr(self, db_session, factories):
        cohort = factories.FeatureCohort()
        user = factories.User()
        db_session.flush()
        feature_cohort_user = FeatureCohortUser(cohort_id=cohort.id, user_id=user.id)
        db_session.add(feature_cohort_user)
        db_session.flush()

        assert (
            repr(feature_cohort_user)
            == f"FeatureCohortUser(id={feature_cohort_user.id!r}, cohort_id={cohort.id!r}, user_id={user.id!r})"
        )
