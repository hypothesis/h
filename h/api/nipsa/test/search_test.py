import copy

from h.api.nipsa import search


def test_nipsa_filter_filters_out_nipsad_annotations():
    """nipsa_filter() filters out annotations with "nipsa": True."""
    assert search.nipsa_filter() == {
        "bool": {
            "should": [
                {'not': {'term': {'nipsa': True}}}
            ]
        }
    }


def test_nipsa_filter_users_own_annotations_are_not_filtered():
    filter_ = search.nipsa_filter(userid="fred")

    assert {'term': {'user': 'fred'}} in (
        filter_["bool"]["should"])


def test_nipsad_annotations_filters_by_userid():
    query = search.nipsad_annotations("test_userid")

    must_clauses = query["query"]["filtered"]["filter"]["bool"]["must"]
    assert {"term": {"user": "test_userid"}} in must_clauses


def test_not_nipsad_annotatopns_filters_by_userid():
    query = search.not_nipsad_annotations("test_userid")

    must_clauses = query["query"]["filtered"]["filter"]["bool"]["must"]
    assert {"term": {"user": "test_userid"}} in must_clauses


def test_nipsad_annotations_filters_by_nipsa():
    query = search.nipsad_annotations("test_userid")

    must_clauses = query["query"]["filtered"]["filter"]["bool"]["must"]
    assert {"term": {"nipsa": True}} in must_clauses


def test_not_nipsad_annotations_filters_by_nipsa():
    query = search.not_nipsad_annotations("test_userid")

    must_clauses = query["query"]["filtered"]["filter"]["bool"]["must"]
    assert {"not": {"term": {"nipsa": True}}} in (
        must_clauses)
