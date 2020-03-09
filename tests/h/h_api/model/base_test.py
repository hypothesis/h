from h.h_api.model.base import Model


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
