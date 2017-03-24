# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from sqlalchemy.orm import subqueryload

from memex import resources
from memex.interfaces import IGroupService

from h import formatters
from h import models
from h import presenters
from h import storage


class AnnotationJSONPresentationService(object):
    def __init__(self, session, authenticated_user, group_svc, links_svc):
        self.session = session
        self.group_svc = group_svc
        self.links_svc = links_svc

        self.formatters = [
            formatters.AnnotationFlagFormatter(self.session, authenticated_user)
        ]

    def present(self, annotation_resource):
        presenter = self.get_presenter(annotation_resource)
        return presenter.asdict()

    def present_all(self, annotation_ids):
        def eager_load_documents(query):
            return query.options(
                subqueryload(models.Annotation.document))

        annotations = storage.fetch_ordered_annotations(
            self.session, annotation_ids, query_processor=eager_load_documents)

        # preload formatters, so they can optimize database access
        for formatter in self.formatters:
            formatter.preload(annotation_ids)

        return [self.present(
                    resources.AnnotationResource(ann, self.group_svc, self.links_svc))
                for ann in annotations]

    def get_presenter(self, annotation_resource):
        presenter = presenters.AnnotationJSONPresenter(annotation_resource)

        for formatter in self.formatters:
            presenter.add_formatter(formatter)

        return presenter


def annotation_json_presentation_service_factory(context, request):
    group_svc = request.find_service(IGroupService)
    links_svc = request.find_service(name='links')
    return AnnotationJSONPresentationService(session=request.db,
                                             authenticated_user=request.authenticated_user,
                                             group_svc=group_svc,
                                             links_svc=links_svc)
