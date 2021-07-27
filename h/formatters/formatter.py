from h.traversal import AnnotationContext


class AnnotationFormatter:
    """Interface for annotation formatters."""

    def preload(self, annotation_ids):
        """
        Preload data to speed up rendering of large batches of annotations.

        :param annotation_ids: List of annotation ids to load
        """

    def format(self, annotation_context: AnnotationContext):
        """
        Render a dict of data to merge into the main presentation data.

        :return: A dict of data
        """
