class TestFlag:
    def test___repr__(self, factories):
        flag = factories.Flag()

        assert (
            repr(flag)
            == f"Flag(id={flag.id!r}, annotation_id={flag.annotation_id!r}, user_id={flag.user_id!r})"
        )
