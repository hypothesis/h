import pytest

from h.services.annotation_json_presentation._formatters.flag import FlagFormatter


class TestFlagFormatter:
    @pytest.mark.parametrize("flagged", (True, False))
    def test_single_item_formatting(self, formatter, annotation, flag_service, flagged):
        flag_service.flagged.return_value = flagged

        result = formatter.format(annotation)

        assert result == {"flagged": flagged}

    def test_unauthenticated_users_do_not_see_flags(self, annotation, flag_service):
        formatter = FlagFormatter(flag_service, user=None)
        flag_service.flagged.return_value = True

        result = formatter.format(annotation)

        assert result == {"flagged": False}

    def test_preloading(self, formatter, factories, flag_service, user):
        annotation, annotation_flagged = factories.Annotation.create_batch(2)
        annotation_ids = [annotation.id, annotation_flagged.id]
        flag_service.all_flagged.return_value = {annotation_flagged.id}

        result = formatter.preload(annotation_ids)

        flag_service.all_flagged.assert_called_once_with(
            user=user, annotation_ids=annotation_ids
        )
        assert result == {annotation.id: False, annotation_flagged.id: True}

    def test_preloading_short_circuits_with_no_user(self, flag_service):
        formatter = FlagFormatter(flag_service, user=None)

        formatter.preload([])

        flag_service.all_flagged.assert_not_called()

    def test_preloading_is_effective_at_preventing_calls(
        self, formatter, annotation, flag_service
    ):
        formatter.preload([annotation.id])
        flag_service.all_flagged.return_value = {}

        result = formatter.format(annotation)

        flag_service.all_flagged.assert_called()
        flag_service.flagged.assert_not_called()
        # Check it still actually works
        assert result == {"flagged": False}

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation()

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def formatter(self, flag_service, user):
        return FlagFormatter(flag_service, user)
