from __future__ import unicode_literals

import newrelic.agent


def send_metric(name, metric):
    """Send a metric to New Relic.

    :arg name: The key name. Only the first 255 characters are retained
    :type name: str
    :arg metric: The string value to add to the current transaction
        Only the first 255 characters are retained.
    :type metric: str, int, float, bool
    """
    newrelic.agent.add_custom_parameter(name, metric)


def record_search_query_param_usage(params, separate_replies):
    """Send search request params to New Relic as metrics.

    :arg params: the request params to record
    :type params: webob.multidict.MultiDict
    :arg separate_replies: Records usage of _separate_replies parameter in the search
    :type separate_replies: bool
    """
    keys = [
        # Record usage of inefficient offset and it's alternative search_after.
        "offset",
        "search_after",
        "sort",
        # Record usage of url/uri (url is an alias of uri).
        "url",
        "uri",
        # Record usage of tags/tag (tags is an alias of tag).
        "tags",
        "tag",
        # Record group and user-these help in identifying slow queries.
        "group",
        "user",
        # Record usage of wildcard feature.
        "wildcard_uri",
    ]
    # Record usage of _separate_replies which will help distinguish client calls
    # for loading the sidebar annotations from other API calls.
    send_metric("es__separate_replies", separate_replies)

    for k in keys:
        if k in params:
            # The New Relic Query Language does not permit _ at the begining
            # and offset is a reserved key word.
            send_metric("es_{}".format(k), params[k])


def record_search_api_usage_metrics(params):
    """Send search API request params to New Relic as metrics.

    :arg params: the request params to record
    :type params: webob.multidict.MultiDict
    """
    keys = [
        # Record usage of inefficient offset and it's alternative search_after.
        "offset",
        "search_after",
        "sort",
        # Record usage of url/uri (url is an alias of uri).
        "url",
        "uri",
        # Record usage of tags/tag (tags is an alias of tag).
        "tags",
        "tag",
        # Record usage of _separate_replies which will help distinguish client calls
        # for loading the sidebar annotations from other api calls.
        "_separate_replies",
        # Record group and user-these help in identifying slow queries.
        "group",
        "user",
        # Record usage of wildcard feature.
        "wildcard_uri",
    ]

    for k in keys:
        if k in params:
            # The New Relic Query Language does not permit _ at the begining
            # and offset is a reserved key word.
            send_metric("es_{}".format(k), params[k])
