# -*- coding: utf-8 -*-
import deform
import mock
import pytest
from pyramid import httpexceptions

from h.groups import views


_SENTINEL = object()


def _mock_request(feature=None, settings=None, params=None,
                  authenticated_userid=_SENTINEL, route_url=None, **kwargs):
    """Return a mock Pyramid request object."""
    params = params or {"foo": "bar"}
    if authenticated_userid is _SENTINEL:
        authenticated_userid = "acct:fred@hypothes.is"
    return mock.Mock(
        feature=feature or (lambda feature: True),
        registry=mock.Mock(settings=settings or {}),
        params=params, POST=params,
        authenticated_userid=authenticated_userid,
        route_url=route_url or mock.Mock(return_value="test-read-url"),
        **kwargs)


def _matchdict():
    """Return a matchdict like the one the group_read route receives."""
    return {"pubid": mock.sentinel.pubid, "slug": mock.sentinel.slug}


# The fixtures required to mock all of create_form()'s dependencies.
create_form_fixtures = pytest.mark.usefixtures('GroupSchema', 'Form')


@create_form_fixtures
def test_create_form_404s_if_groups_feature_is_off():
    with pytest.raises(httpexceptions.HTTPNotFound):
        views.create_form(_mock_request(feature=lambda feature: False))


@create_form_fixtures
def test_create_form_creates_form_with_GroupSchema(GroupSchema, Form):
    test_schema = mock.Mock()
    GroupSchema.return_value = mock.Mock(
        bind=mock.Mock(return_value=test_schema))

    views.create_form(request=_mock_request())

    assert Form.call_args[0][0] == test_schema


@create_form_fixtures
def test_create_form_returns_form(Form):
    test_form = mock.Mock()
    Form.return_value = test_form

    result = views.create_form(request=_mock_request())

    assert result["form"] == test_form.render.return_value


# The fixtures required to mock all of create()'s dependencies.
create_fixtures = pytest.mark.usefixtures('GroupSchema', 'Form', 'Group',
                                          'session_model')


@create_fixtures
def test_create_404s_if_groups_feature_is_off():
    with pytest.raises(httpexceptions.HTTPNotFound):
        views.create(_mock_request(feature=lambda feature: False))


@create_fixtures
def test_create_inits_form_with_schema(GroupSchema, Form):
    schema = mock.Mock()
    GroupSchema.return_value = mock.Mock(bind=mock.Mock(return_value=schema))

    views.create(request=_mock_request())

    assert Form.call_args[0][0] == schema


@create_fixtures
def test_create_validates_form(Form):
    Form.return_value = form = mock.Mock()
    form.validate.return_value = {"name": "new group"}
    request = _mock_request()

    views.create(request)

    form.validate.assert_called_once_with(request.params.items())


@create_fixtures
def test_create_rerenders_form_on_validation_failure(Form):
    Form.return_value = form = mock.Mock()
    form.validate.side_effect = deform.ValidationFailure(None, None, None)

    result = views.create(_mock_request())

    assert result['form'] == form.render.return_value


@create_fixtures
def test_create_gets_user_with_authenticated_id(Form):
    """It uses the "name" from the validated data to create a new group."""
    Form.return_value = mock.Mock(validate=lambda data: {"name": "test-group"})
    request = _mock_request()
    type(request).authenticated_user = user_property = mock.PropertyMock()

    views.create(request)

    user_property.assert_called_once_with()


@create_fixtures
def test_create_uses_name_from_validated_data(Form, Group):
    """It uses the "name" from the validated data to create a new group."""
    Form.return_value = mock.Mock(validate=lambda data: {"name": "test-group"})
    request = _mock_request()
    request.authenticated_user = user = mock.Mock()

    views.create(request)

    Group.assert_called_once_with(name="test-group", creator=user)


@create_fixtures
def test_create_adds_group_to_db(Group):
    """It should add the new group to the database session."""
    group = mock.Mock(id=6)
    Group.return_value = group
    request = _mock_request()

    views.create(request)

    request.db.add.assert_called_once_with(group)


@create_fixtures
def test_create_redirects_to_group_read_page(Group):
    """After successfully creating a new group it should redirect."""
    group = mock.Mock(id='test-id', slug='test-slug')
    Group.return_value = group
    request = _mock_request()

    result = views.create(request)

    assert isinstance(result, httpexceptions.HTTPRedirection)


@create_fixtures
def test_create_with_non_ascii_name():
    views.create(_mock_request(params={"name": u"☆ ßüper Gröup ☆"}))


@create_fixtures
def test_create_publishes_join_event(Group, session_model):
    group = mock.Mock(pubid=mock.sentinel.pubid)
    Group.return_value = group
    request = _mock_request()

    views.create(request)

    request.get_queue_writer().publish.assert_called_once_with('user', {
        'type': 'group-join',
        'userid': request.authenticated_userid,
        'group': group.pubid,
        'session_model': session_model(),
    })


# The fixtures required to mock all of read()'s dependencies.
read_fixtures = pytest.mark.usefixtures('search', 'Group', 'renderers', 'uri')


@read_fixtures
def test_read_404s_if_groups_feature_is_off():
    with pytest.raises(httpexceptions.HTTPNotFound):
        views.read(_mock_request(feature=lambda feature: False))


@read_fixtures
def test_read_gets_group_by_pubid(Group):
    views.read(_mock_request(matchdict={'pubid': 'abc', 'slug': 'snail'}))

    Group.get_by_pubid.assert_called_once_with('abc')


@read_fixtures
def test_read_404s_when_group_does_not_exist(Group):
    Group.get_by_pubid.return_value = None

    with pytest.raises(httpexceptions.HTTPNotFound):
        views.read(_mock_request(matchdict=_matchdict()))


@read_fixtures
def test_read_without_slug_redirects(Group):
    """/groups/<pubid> should redirect to /groups/<pubid>/<slug>."""
    group = Group.get_by_pubid.return_value = mock.Mock()
    matchdict = {"pubid": "1"}  # No slug.
    request = _mock_request(matchdict=matchdict)

    result = views.read(request)

    assert isinstance(result, httpexceptions.HTTPRedirection)


@read_fixtures
def test_read_with_wrong_slug_redirects(Group):
    """/groups/<pubid>/<wrong> should redirect to /groups/<pubid>/<slug>."""
    group = Group.get_by_pubid.return_value = mock.Mock(slug="my-group")
    matchdict = {"pubid": "1", "slug": "my-gro"}  # Wrong slug.
    request = _mock_request(matchdict=matchdict)

    result = views.read(request)

    assert isinstance(result, httpexceptions.HTTPRedirection)


@read_fixtures
def test_read_if_not_logged_in_renders_share_group_page(Group, renderers):
    """If not logged in should render the "Login to join this group" page."""
    Group.get_by_pubid.return_value = mock.Mock(slug=mock.sentinel.slug)
    request = _mock_request(authenticated_userid=None, matchdict=_matchdict())

    views.read(request)

    assert renderers.render_to_response.call_args[1]['renderer_name'] == (
        'h:groups/templates/join.html.jinja2')


@read_fixtures
def test_read_if_not_logged_in_passes_group(Group, renderers):
    """It should pass the group to the template."""
    g = Group.get_by_pubid.return_value = mock.Mock(slug=mock.sentinel.slug)
    request = _mock_request(authenticated_userid=None, matchdict=_matchdict())

    views.read(request)

    assert renderers.render_to_response.call_args[1]['value']['group'] == g


@read_fixtures
def test_read_if_not_logged_in_returns_response(
        Group, renderers):
    """It should return the response from render_to_response()."""
    Group.get_by_pubid.return_value = mock.Mock(slug=mock.sentinel.slug)
    request = _mock_request(authenticated_userid=None, matchdict=_matchdict())
    renderers.render_to_response.return_value = mock.sentinel.response

    response = views.read(request)

    assert response == mock.sentinel.response


@read_fixtures
def test_read_if_not_a_member_renders_template(Group, renderers):
    """It should render the "Join this group" template."""
    request = _mock_request(matchdict=_matchdict())
    Group.get_by_pubid.return_value = mock.Mock(slug=mock.sentinel.slug)
    user = request.authenticated_user = mock.Mock()
    user.groups = []  # The user isn't a member of the group.

    views.read(request)

    assert renderers.render_to_response.call_args[1]['renderer_name'] == (
        'h:groups/templates/join.html.jinja2')


@read_fixtures
def test_read_if_not_a_member_passes_group_to_template(Group, renderers):
    """It should get the join URL and pass it to the template."""
    request = _mock_request(matchdict=_matchdict())
    g = Group.get_by_pubid.return_value = mock.Mock(slug=mock.sentinel.slug)
    user = request.authenticated_user = mock.Mock()
    user.groups = []  # The user isn't a member of the group.

    views.read(request)

    assert renderers.render_to_response.call_args[1]['value']['group'] == g


@read_fixtures
def test_read_if_not_a_member_passes_join_url_to_template(Group, renderers):
    """It should get the join URL and pass it to the template."""
    request = _mock_request(matchdict=_matchdict())
    request.route_url.return_value = mock.sentinel.join_url
    Group.get_by_pubid.return_value = mock.Mock(slug=mock.sentinel.slug)
    user = request.authenticated_user = mock.Mock()
    user.groups = []  # The user isn't a member of the group.

    views.read(request)

    assert renderers.render_to_response.call_args[1]['value']['join_url'] == (
        mock.sentinel.join_url)


@read_fixtures
def test_read_if_not_a_member_returns_response(Group, renderers):
    """It should return the response from render_to_response()."""
    request = _mock_request(matchdict=_matchdict())
    Group.get_by_pubid.return_value = mock.Mock(slug=mock.sentinel.slug)
    user = request.authenticated_user = mock.Mock()
    user.groups = []  # The user isn't a member of the group.
    renderers.render_to_response.return_value = mock.sentinel.response

    assert views.read(request) == mock.sentinel.response


@read_fixtures
def test_read_if_already_a_member_renders_template(Group, renderers):
    """It should render the "Share this group" template."""
    request = _mock_request(matchdict=_matchdict())
    g = Group.get_by_pubid.return_value = mock.Mock(slug=mock.sentinel.slug)
    user = request.authenticated_user = mock.Mock()
    user.groups = [g]  # The user is a member of the group.

    views.read(request)
    assert renderers.render_to_response.call_args[1]['renderer_name'] == (
        'h:groups/templates/share.html.jinja2')


@read_fixtures
def test_read_if_already_a_member_passes_group(Group, renderers):
    """It passes the group to the template."""
    request = _mock_request(matchdict=_matchdict())
    g = Group.get_by_pubid.return_value = mock.Mock(slug=mock.sentinel.slug)
    user = request.authenticated_user = mock.Mock()
    user.groups = [g]  # The user is a member of the group.

    views.read(request)

    assert renderers.render_to_response.call_args[1]['value']['group'] == g


@read_fixtures
def test_read_if_already_a_member_returns_response(Group, renderers):
    """It should return the response from render_to_response()."""
    request = _mock_request(matchdict=_matchdict())
    g = Group.get_by_pubid.return_value = mock.Mock(slug=mock.sentinel.slug)
    user = request.authenticated_user = mock.Mock()
    user.groups = [g]  # The user is a member of the group.
    renderers.render_to_response.return_value = mock.sentinel.response

    assert views.read(request) == mock.sentinel.response


@read_fixtures
def test_read_calls_search(Group, search, renderers):
    """It should call search() to get the annotations."""
    request = _mock_request(matchdict=_matchdict())
    g = Group.get_by_pubid.return_value = mock.Mock(slug=mock.sentinel.slug)
    user = request.authenticated_user = mock.Mock()
    user.groups = [g]  # The user is a member of the group.
    renderers.render_to_response.return_value = mock.sentinel.response

    views.read(request)

    search.search.assert_called_once_with(
            request, private=False, params={"group": g.pubid, "limit": 1000})


@read_fixtures
def test_read_calls_normalize(Group, search, renderers, uri):
    """It shold call normalize() with each of the URIs from search()."""
    request = _mock_request(matchdict=_matchdict())
    g = Group.get_by_pubid.return_value = mock.Mock(slug=mock.sentinel.slug)
    user = request.authenticated_user = mock.Mock()
    user.groups = [g]  # The user is a member of the group.
    renderers.render_to_response.return_value = mock.sentinel.response
    search.search.return_value = {
        "rows": [
            mock.Mock(uri="uri_1"),
            mock.Mock(uri="uri_2"),
            mock.Mock(uri="uri_3"),
        ]
    }

    views.read(request)

    assert uri.normalize.call_args_list == [
        mock.call("uri_1"), mock.call("uri_2"), mock.call("uri_3")]


@read_fixtures
def test_read_returns_document_links(Group, search, renderers, uri):
    """It should return the list of document links."""
    request = mock.Mock(matchdict=_matchdict())
    g = Group.get_by_pubid.return_value = mock.Mock(slug=mock.sentinel.slug)
    user = request.authenticated_user = mock.Mock()
    user.groups = [g]  # The user is a member of the group.
    annotations = [
        mock.Mock(uri="uri_1", document_link="document_link_1"),
        mock.Mock(uri="uri_2", document_link="document_link_2"),
        mock.Mock(uri="uri_3", document_link="document_link_3")
    ]
    search.search.return_value = {"rows": annotations}

    def normalize(uri):
        return uri + "_normalized"
    uri.normalize.side_effect = normalize

    views.read(request)

    assert (
        renderers.render_to_response.call_args[1]['value']['document_links']
        == ["document_link_1", "document_link_2", "document_link_3"])


@read_fixtures
def test_read_duplicate_documents_are_removed(Group, search, renderers, uri):
    """

    If the group has multiple annotations whose uris all normalize to the same
    uri, only the document_link of the first one of these annotations should be
    sent to the template.

    """
    request = mock.Mock(matchdict=_matchdict())
    g = Group.get_by_pubid.return_value = mock.Mock(slug=mock.sentinel.slug)
    user = request.authenticated_user = mock.Mock()
    user.groups = [g]  # The user is a member of the group.
    annotations = [
        mock.Mock(uri="uri_1", document_link="document_link_1"),
        mock.Mock(uri="uri_2", document_link="document_link_2"),
        mock.Mock(uri="uri_3", document_link="document_link_3")
    ]
    search.search.return_value = {"rows": annotations}

    def normalize(uri):
        # All three annotations' URIs normalize to the same URI.
        return "normalized"
    uri.normalize.side_effect = normalize

    views.read(request)

    assert (
        renderers.render_to_response.call_args[1]['value']['document_links']
        == ["document_link_1"])


@read_fixtures
def test_read_documents_are_truncated(Group, search, renderers, uri):
    """It should send at most 25 document links to the template."""
    request = mock.Mock(matchdict=_matchdict())
    g = Group.get_by_pubid.return_value = mock.Mock(slug=mock.sentinel.slug)
    user = request.authenticated_user = mock.Mock()
    user.groups = [g]  # The user is a member of the group.
    annotations = [
        mock.Mock(uri="uri_{n}".format(n=n),
                  document_link="document_link_{n}".format(n=n))
        for n in range(0, 50)
    ]
    search.search.return_value = {"rows": annotations}

    def normalize(uri):
        # All three annotations' URIs normalize to the same URI.
        return uri + "_normalized"
    uri.normalize.side_effect = normalize

    views.read(request)

    assert (len(
        renderers.render_to_response.call_args[1]['value']['document_links'])
        == 25)

# The fixtures required to mock all of join()'s dependencies.
join_fixtures = pytest.mark.usefixtures('Group', 'session_model')


@join_fixtures
def test_join_404s_if_groups_feature_is_off():
    with pytest.raises(httpexceptions.HTTPNotFound):
        views.join(_mock_request(feature=lambda feature: False))


@join_fixtures
def test_join_gets_group_by_pubid(Group):
    views.join(_mock_request(matchdict={'pubid': 'twibble', 'slug': 'snail'}))

    Group.get_by_pubid.assert_called_once_with("twibble")


@join_fixtures
def test_join_404s_if_group_not_found(Group):
    Group.get_by_pubid.return_value = None

    with pytest.raises(httpexceptions.HTTPNotFound):
        views.join(_mock_request(matchdict=_matchdict()))


@join_fixtures
def test_join_gets_user():
    request = _mock_request(matchdict=_matchdict())
    type(request).authenticated_user = user_property = mock.PropertyMock()

    views.join(request)

    user_property.assert_called_once_with()


@join_fixtures
def test_join_adds_user_to_group_members(Group):
    Group.get_by_pubid.return_value = group = mock.Mock()
    request = _mock_request(
        matchdict=_matchdict(), authenticated_user=mock.sentinel.user)

    views.join(request)

    group.members.append.assert_called_once_with(mock.sentinel.user)


@join_fixtures
def test_join_redirects_to_group_page(Group):
    slug = "test-slug"
    group = Group.get_by_pubid.return_value = mock.Mock(slug=slug)
    request = _mock_request(matchdict=_matchdict())

    result = views.join(request)

    assert isinstance(result, httpexceptions.HTTPRedirection)


@join_fixtures
def test_join_publishes_join_event(Group, session_model):
    group = mock.Mock(pubid = mock.sentinel.pubid)
    Group.get_by_pubid.return_value = group
    request = _mock_request(matchdict=_matchdict())

    views.join(request)

    request.get_queue_writer().publish.assert_called_once_with('user', {
        'type': 'group-join',
        'userid': request.authenticated_userid,
        'group': mock.sentinel.pubid,
        'session_model': session_model(),
    })


leave_fixtures = pytest.mark.usefixtures('Group', 'session_model')


@leave_fixtures
def test_leave_removes_user_from_group_members(Group):
    user = mock.sentinel.user
    group = mock.Mock()
    group.members = [user]
    Group.get_by_pubid.return_value = group
    request = _mock_request(
        matchdict=_matchdict(), authenticated_user=user)

    result = views.leave(request)

    assert(group.members == [])


@leave_fixtures
def test_leave_returns_not_found_if_user_not_in_group(Group):
    group = mock.Mock(members=[])
    Group.get_by_pubid.return_value = group
    request = _mock_request(matchdict=_matchdict(), user=mock.sentinel.user)

    with pytest.raises(httpexceptions.HTTPNotFound):
        result = views.leave(request)


@leave_fixtures
def test_leave_publishes_leave_event(Group, session_model):
    group = mock.Mock(pubid=mock.sentinel.pubid,
                      members=[mock.sentinel.user])
    Group.get_by_pubid.return_value = group
    request = _mock_request(
        matchdict=_matchdict(), authenticated_user=mock.sentinel.user)

    views.leave(request)

    request.get_queue_writer().publish.assert_called_once_with('user', {
        'type': 'group-leave',
        'userid': request.authenticated_userid,
        'group': mock.sentinel.pubid,
        'session_model': session_model(),
    })


@pytest.fixture
def Form(request):
    patcher = mock.patch('h.groups.views.deform.Form', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def GroupSchema(request):
    patcher = mock.patch('h.groups.views.schemas.GroupSchema', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def Group(request):
    patcher = mock.patch('h.groups.views.models.Group', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def session_model(request):
    patcher = mock.patch('h.session.model')
    request.addfinalizer(patcher.stop)
    return patcher.start()

@pytest.fixture
def renderers(request):
    patcher = mock.patch('h.groups.views.renderers', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def search(request):
    patcher = mock.patch('h.groups.views.search', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def uri(request):
    patcher = mock.patch('h.groups.views.uri', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
