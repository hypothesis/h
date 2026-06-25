class TestCheckpoint:
    def test___repr__(self, factories):
        checkpoint = factories.Checkpoint()

        assert repr(checkpoint) == (
            f"Checkpoint(id={checkpoint.id!r}, "
            f"group_id={checkpoint.group_id!r}, "
            f"previous_checkpoint_id={checkpoint.previous_checkpoint_id!r}, "
            f"reveal_date={checkpoint.reveal_date!r})"
        )
