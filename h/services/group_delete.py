from h.models import Annotation


class DeletePublicGroupError(Exception):
    pass


class GroupDeleteService:
    def __init__(self, request, annotation_delete_service):
        self.request = request
        self._annotation_delete_service = annotation_delete_service

    def delete(self, group):
        """
        Delete a group.

        Including its membership relations and all annotations in the group.
        """

        self._delete_annotations(group)
        self.request.db.delete(group)

    def _delete_annotations(self, group):
        if group.pubid == "__world__":
            raise DeletePublicGroupError("Public group can not be deleted")

        annotations = self.request.db.query(Annotation).filter_by(groupid=group.pubid)
        self._annotation_delete_service.delete_annotations(annotations)


def service_factory(_context, request):
    annotation_delete_service = request.find_service(name="annotation_delete")
    return GroupDeleteService(request, annotation_delete_service)
