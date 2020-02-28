from unittest.mock import create_autospec

import pytest

from h.h_api.model.base import Model
from h.h_api.schema import Validator


class TestModel:
    def test_initialisation(self):
        # This looks dumb now... but more is coming
        data = {"a": 1}
        model = Model(raw=data)

        assert model.raw is data

    def test_extract_raw(self):
        data = {"a": 1}
        model = Model(raw=data)

        assert Model.extract_raw(data) is data
        assert Model.extract_raw(model) is data

    def test_dict_from_populated(self):
        result = Model.dict_from_populated(a=1, b=None, c="", d=[], e={})

        assert result == {"a": 1, "c": "", "d": [], "e": {}}

    def test_it_applies_schema(self, ModelClass):
        data = {"data": 1}
        model = ModelClass(data)

        model.validator.validate_all.assert_called_once_with(data)

    @pytest.fixture
    def ModelClass(self):
        class ModelClass(Model):
            # TODO! - This doesn't work as JSONSchema doesn't like being mocked
            validator = create_autospec(Validator, instance=True)

        return ModelClass
