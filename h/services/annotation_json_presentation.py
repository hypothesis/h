# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from sqlalchemy.orm import subqueryload

from memex import resources
from memex.interfaces import IGroupService

from h import models
from h import presenters
from h import storage


class AnnotationJSONPresentationService(object):
    def __init__(self, session, group_svc, links_svc):
        self.session = session
        self.group_svc = group_svc
        self.links_svc = links_svc

    def present(self, annotation_resource):
        presenter = presenters.AnnotationJSONPresenter(annotation_resource)
        return presenter.asdict()

    def present_all(self, annotation_ids):
        def eager_load_documents(query):
            return query.options(
                subqueryload(models.Annotation.document))

        annotations = storage.fetch_ordered_annotations(
            self.session, annotation_ids, query_processor=eager_load_documents)

        return [self.present(
                    resources.AnnotationResource(ann, self.group_svc, self.links_svc))
                for ann in annotations]


def annotation_json_presentation_service_factory(context, request):
    group_svc = request.find_service(IGroupService)
    links_svc = request.find_service(name='links')
    return AnnotationJSONPresentationService(request.db,
                                             group_svc,
                                             links_svc)
