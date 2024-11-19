def test_repr(db_session, factories):
    annotation_slim = factories.AnnotationSlim()
    db_session.flush()

    assert repr(annotation_slim) == f"AnnotationSlim(id={annotation_slim.id!r})"
