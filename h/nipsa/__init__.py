def includeme(config):
    # Register the transform_annotation subscriber so that nipsa fields are
    # written into annotations on save.
    config.add_subscriber(
        "h.nipsa.subscribers.nipsa_transform_annotation",
        "h.events.AnnotationTransformEvent",
    )
