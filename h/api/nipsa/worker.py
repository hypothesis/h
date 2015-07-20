"""Worker functions for the NIPSA feature."""
import json

from elasticsearch import helpers
import annotator

from h.api.nipsa import search as nipsa_search


def add_nipsa_action(annotation):
    """Return an Elasticsearch action for adding NIPSA to the annotation."""
    return {
        "_op_type": "update",
        "_index": annotator.es.index,
        "_type": "annotation",
        "_id": annotation["_id"],
        "doc": {"not_in_public_site_areas": True}
    }


def remove_nipsa_action(annotation):
    """Return an Elasticsearch action to remove NIPSA from the annotation."""
    return {
        "_op_type": "update",
        "_index": annotator.es.index,
        "_type": "annotation",
        "_id": annotation["_id"],
        "script": "ctx._source.remove(\"not_in_public_site_areas\")"
    }


def add_or_remove_nipsa(userid, action, es_client):
    """Add/remove the NIPSA flag to/from all of the user's annotations."""
    assert action in ("add_nipsa", "remove_nipsa")
    if action == "add_nipsa":
        query = nipsa_search.not_nipsad_annotations(userid)
        action_func = add_nipsa_action
    else:
        query = nipsa_search.nipsad_annotations(userid)
        action_func = remove_nipsa_action

    annotations = helpers.scan(client=es_client, query=query, fields=[])
    actions = [action_func(a) for a in annotations]
    helpers.bulk(client=es_client, actions=actions)


def worker(request):
    """Worker function for NIPSA'ing and un-NIPSA'ing users.

    This is a worker function that listens for user-related NIPSA messages on
    NSQ (when the NIPSA API adds the NIPSA flag to or removes the NIPSA flag
    from a user) and adds the NIPSA flag to or removes the NIPSA flag from all
    of the NIPSA'd user's annotations.

    """
    def handle_message(_, message):
        """Handle a message on the "nipsa_users_annotations" channel."""
        add_or_remove_nipsa(
            es_client=request.es_client,
            **json.loads(message.body))

    reader = request.get_queue_reader(
        "nipsa_user_requests", "nipsa_users_annotations")
    reader.on_message.connect(handle_message)
    reader.start(block=True)
