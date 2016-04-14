# -*- coding: utf-8 -*-
"""Worker functions for the NIPSA feature."""

from elasticsearch import helpers

from h.celery import celery
from h.celery import get_task_logger
from h.nipsa import search

log = get_task_logger(__name__)


def add_nipsa_action(index, annotation):
    """Return an Elasticsearch action for adding NIPSA to the annotation."""
    return {
        "_op_type": "update",
        "_index": index,
        "_type": "annotation",
        "_id": annotation["_id"],
        "doc": {"nipsa": True}
    }


def remove_nipsa_action(index, annotation):
    """Return an Elasticsearch action to remove NIPSA from the annotation."""
    source = annotation["_source"].copy()
    source.pop("nipsa", None)
    return {
        "_op_type": "index",
        "_index": index,
        "_type": "annotation",
        "_id": annotation["_id"],
        "_source": source,
    }


def bulk_update_annotations(client, query, action):
    """
    Bulk update annotations matching a query with a passed action function.

    This uses Elasticsearch's scan/scroll query and bulk update APIs to perform
    updates to a set of annotations. Annotations matching the passed query will
    be passed one-by-one to the passed "action" function, which must return an
    action dictionary in the form dictated by the Elasticsearch bulk update
    API.

    :param client: the Elasticsearch client instance
    :type client: h.api.search.client.Client

    :param query: a query dict selecting annotations to update
    :type query: dict

    :param action: a function mapping annotations to bulk actions
    :type action: function
    """
    annotations = helpers.scan(client=client.conn,
                               index=client.index,
                               query=query)
    actions = [action(client.index, a) for a in annotations]
    helpers.bulk(client=client.conn, actions=actions)


@celery.task
def add_nipsa(userid):
    log.info("setting nipsa flag for user annotations: %s", userid)
    bulk_update_annotations(celery.request.legacy_es,
                            search.not_nipsad_annotations(userid),
                            add_nipsa_action)


@celery.task
def remove_nipsa(userid):
    log.info("clearing nipsa flag for user annotations: %s", userid)
    bulk_update_annotations(celery.request.legacy_es,
                            search.nipsad_annotations(userid),
                            remove_nipsa_action)
