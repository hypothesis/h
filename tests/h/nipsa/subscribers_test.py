from unittest.mock import create_autospec

import pytest

from h.events import AnnotationTransformEvent
from h.nipsa.subscribers import nipsa_transform_annotation
from h.services.nipsa import NipsaService


class TestTransformAnnotation:
    def test_if_user_is_missing_nothing_happens(self, event, nipsa_service):
        event.annotation_dict.pop("user")

        nipsa_transform_annotation(event)

        assert "nipsa" not in event.annotation_dict
        nipsa_service.is_flagged.assert_not_called()

    @pytest.mark.parametrize("flagged", [True, False])
    def test_nipsa_status_is_added_based_on_flagged(
        self, event, nipsa_service, flagged
    ):
        nipsa_service.is_flagged.return_value = flagged

        nipsa_transform_annotation(event)

        nipsa_service.is_flagged.assert_called_once_with(event.annotation_dict["user"])
        assert bool(event.annotation_dict.get("nipsa")) == flagged

    @pytest.fixture
    def event(self, pyramid_request, factories):
        return AnnotationTransformEvent(
            request=pyramid_request,
            annotation=factories.Annotation(),
            annotation_dict={"user": "username"},
        )

    @pytest.fixture(autouse=True)
    def nipsa_service(self, pyramid_config):
        nipsa_service = create_autospec(NipsaService, instance=True)
        nipsa_service.is_flagged.return_value = False
        pyramid_config.register_service(nipsa_service, name="nipsa")
        return nipsa_service
