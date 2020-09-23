def nipsa_transform_annotation(event):
    """Mark moderated or flagged annotations.

    Adds `{"nipsa": True}` to an annotation.
    """
    user = event.annotation_dict.get("user")
    if user is None:
        return

    nipsa_service = event.request.find_service(name="nipsa")
    if nipsa_service.is_flagged(user):
        event.annotation_dict["nipsa"] = True
