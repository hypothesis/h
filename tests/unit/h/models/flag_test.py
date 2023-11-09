from h.models.flag import Flag


class TestFlag:
    def test___repr__(self):
        flag = Flag(annotation_id=123, user_id=456)

        assert repr(flag) == "<Flag annotation_id=123 user_id=456>"
