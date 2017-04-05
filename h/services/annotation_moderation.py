# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h import models


class AnnotationModerationService(object):
    def __init__(self, session):
        self.session = session

    def hidden(self, annotation_id):
        """
        Check if an annotation id is hidden.

        :param annotation_id: The id of the annotation to check.
        :type annotation: unicode

        :returns: true/false boolean
        :rtype: bool
        """
        q = self.session.query(models.AnnotationModeration) \
                        .filter_by(annotation_id=annotation_id)
        return self.session.query(q.exists()).scalar()

    def hide(self, annotation):
        """
        Hide an annotation from other users.

        This hides the given annotation from anybody except its author and the
        group moderators.

        In case the given annotation already has a moderation flag, this method
        is a no-op.

        :param annotation: The annotation to hide from others.
        :type annotation: h.models.Annotation
        """

        if self.hidden(annotation.id):
            return

        mod = models.AnnotationModeration(annotation=annotation)
        self.session.add(mod)

    def unhide(self, annotation):
        """
        Show a hidden annotation again to other users.

        In case the given annotation is not moderated, this method is a no-op.

        :param annotation: The annotation to unhide.
        :type annotation: h.models.Annotation
        """

        self.session.query(models.AnnotationModeration) \
                    .filter_by(annotation=annotation) \
                    .delete()


def annotation_moderation_service_factory(context, request):
    return AnnotationModerationService(request.db)
