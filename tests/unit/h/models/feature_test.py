from unittest import mock

import pytest

from h.models import Feature


@pytest.mark.usefixtures("features_override")
class TestFeature:
    def test_description_returns_hardcoded_description(self):
        feat = Feature(name="notification")

        assert feat.description == "A test flag for testing with."

    def test_all_creates_annotations_that_dont_exist(self, db_session):
        features = Feature.all(db_session)

        assert len(features) == 1
        assert features[0].name == "notification"

    def test_all_only_returns_current_flags(self, db_session):
        """The .all() method should only return named current feature flags."""
        new, old = [
            Feature(name="notification"),
            Feature(name="somethingelse"),
        ]
        db_session.add_all([new, old])
        db_session.flush()

        features = Feature.all(db_session)

        assert len(features) == 1
        assert features[0].name == "notification"

    def test_remove_old_flag_removes_old_flags(self, db_session):
        """
        The remove_old_flags function should remove unknown flags.

        New flags should be left alone, but completely
        unknown flags should be removed.
        """
        new, old = [
            Feature(name="notification"),
            Feature(name="somethingelse"),
        ]
        db_session.add_all([new, old])
        db_session.flush()

        Feature.remove_old_flags(db_session)

        remaining = {f.name for f in db_session.query(Feature).all()}
        assert remaining == {"notification"}

    @pytest.fixture
    def features_override(self, request):
        # Replace the primary FEATURES dictionary for the duration of testing...
        patcher = mock.patch.dict(
            "h.models.feature.FEATURES",
            {"notification": "A test flag for testing with."},
            clear=True,
        )
        patcher.start()
        request.addfinalizer(patcher.stop)
