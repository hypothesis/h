from h.tasks.indexer import add_annotation, delete_annotation


def subscribe_annotation_event(event):
    if event.action in ["create", "update"]:
        add_annotation.delay(event.annotation_id)
    elif event.action == "delete":
        delete_annotation.delay(event.annotation_id)
