import copy

from h.api.nipsa import search


def test_nipsa_filter_preserves_original_query():
    original_query = {"query": {"foo": "bar"}}

    filtered_query = search.nipsa_filter(original_query)

    assert filtered_query["query"]["filtered"]["query"] == (
        original_query["query"])


def test_nipsa_filter_does_not_modify_original_dict():
    original_query = {"query": {"foo": "bar"}}
    copy_ = copy.deepcopy(original_query)

    filtered_query = search.nipsa_filter(original_query)

    assert original_query == copy_


def test_nipsa_filter_filters_out_nipsad_annotations():
    """nipsa_filter() filters out annotations with "nipsa": True."""
    query = search.nipsa_filter({"query": {"foo": "bar"}})

    assert query["query"]["filtered"]["filter"] == {
        "bool": {
            "should": [
                {'not': {'term': {'not_in_public_site_areas': True}}}
            ]
        }
    }


def test_build_query_users_own_annotations_are_not_filtered():
    query = search.nipsa_filter({"query": {"foo": "bar"}}, userid="fred")

    assert {'term': {'user': 'fred'}} in (
        query["query"]["filtered"]["filter"]["bool"]["should"])


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
    assert {"term": {"not_in_public_site_areas": True}} in must_clauses


def test_not_nipsad_annotations_filters_by_nipsa():
    query = search.not_nipsad_annotations("test_userid")

    must_clauses = query["query"]["filtered"]["filter"]["bool"]["must"]
    assert {"not": {"term": {"not_in_public_site_areas": True}}} in (
        must_clauses)
