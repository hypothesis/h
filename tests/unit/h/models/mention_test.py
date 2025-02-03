def test_repr(factories):
    annotation = factories.Annotation()
    mention = factories.Mention(annotation=annotation)

    assert (
        repr(mention)
        == f"Mention(id={mention.id}, annotation_id={mention.annotation.id!r}, user_id={mention.user.id})"
    )
