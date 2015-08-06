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
        registry=mock.Mock(settings=settings or {
            "h.hashids.salt": "test salt"}),
        params=params, POST=params,
        authenticated_userid=authenticated_userid,
        route_url=route_url or mock.Mock(return_value="test-read-url"),
        **kwargs)


def _matchdict():
    """Return a matchdict like the one the group_read route receives."""
    return {"hashid": mock.sentinel.hashid, "slug": mock.sentinel.slug}


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

    Form.assert_called_once_with(test_schema)


@create_form_fixtures
def test_create_form_returns_form(Form):
    test_form = mock.Mock()
    Form.return_value = test_form

    template_data = views.create_form(request=_mock_request())

    assert template_data["form"] == test_form


@create_form_fixtures
def test_create_form_returns_empty_form_data(Form):
    test_form = mock.Mock()
    Form.return_value = test_form

    template_data = views.create_form(request=_mock_request())

    assert template_data["data"] == {}


# The fixtures required to mock all of create()'s dependencies.
create_fixtures = pytest.mark.usefixtures(
    'GroupSchema', 'Form', 'Group', 'User', 'logic')


@create_fixtures
def test_create_404s_if_groups_feature_is_off():
    with pytest.raises(httpexceptions.HTTPNotFound):
        views.create(_mock_request(feature=lambda feature: False))


@create_fixtures
def test_create_inits_form_with_schema(GroupSchema, Form):
    schema = mock.Mock()
    GroupSchema.return_value = mock.Mock(bind=mock.Mock(return_value=schema))

    views.create(request=_mock_request())

    Form.assert_called_once_with(schema)


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
    params = {"foo": "bar"}

    template_data = views.create(_mock_request())

    assert template_data['form'] == form
    assert template_data['data'] == params


@create_fixtures
def test_create_gets_user_with_authenticated_id(Form, User):
    """It uses the "name" from the validated data to create a new group."""
    Form.return_value = mock.Mock(validate=lambda data: {"name": "test-group"})
    request = _mock_request()

    views.create(request)

    User.get_by_id.assert_called_once_with(
        request, request.authenticated_userid)


@create_fixtures
def test_create_uses_name_from_validated_data(Form, User, Group):
    """It uses the "name" from the validated data to create a new group."""
    Form.return_value = mock.Mock(validate=lambda data: {"name": "test-group"})
    User.get_by_id.return_value = user = mock.Mock()

    views.create(_mock_request())

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
def test_create_redirects_to_group_read_page(Group, logic):
    """After successfully creating a new group it should redirect."""
    group = mock.Mock(id='test-id', slug='test-slug')
    Group.return_value = group
    request = _mock_request()
    logic.url_for_group.return_value = "test-read-url"

    redirect = views.create(request)

    logic.url_for_group.assert_called_once_with(request, group)
    assert redirect.status_int == 303
    assert redirect.location == "test-read-url"


@create_fixtures
def test_create_with_non_ascii_name():
    views.create(_mock_request(params={"name": u"☆ ßüper Gröup ☆"}))


# The fixtures required to mock all of read()'s dependencies.
read_fixtures = pytest.mark.usefixtures(
    'Group', 'hashids', 'User', 'renderers', 'logic')


@read_fixtures
def test_read_404s_if_groups_feature_is_off():
    with pytest.raises(httpexceptions.HTTPNotFound):
        views.read(_mock_request(feature=lambda feature: False))


@read_fixtures
def test_read_decodes_hashid(hashids):
    matchdict = _matchdict()
    request = _mock_request(matchdict=matchdict)

    views.read(request)

    hashids.decode.assert_called_once_with(
        request, "h.groups", matchdict["hashid"])


@read_fixtures
def test_read_gets_group_by_id(Group, hashids):
    hashids.decode.return_value = 1

    views.read(_mock_request(matchdict=_matchdict()))

    Group.get_by_id.assert_called_once_with(1)


@read_fixtures
def test_read_404s_when_group_does_not_exist(Group):
    Group.get_by_id.return_value = None

    with pytest.raises(httpexceptions.HTTPNotFound):
        views.read(_mock_request(matchdict=_matchdict()))


@read_fixtures
def test_read_without_slug_redirects(Group, logic):
    """/groups/<hashid> should redirect to /groups/<hashid>/<slug>."""
    group = Group.get_by_id.return_value = mock.Mock()
    matchdict = {"hashid": "1"}  # No slug.
    request = _mock_request(matchdict=matchdict)
    logic.url_for_group.return_value = "/1/my-group"

    redirect = views.read(request)

    logic.url_for_group.assert_called_once_with(request, group)
    assert redirect.location == "/1/my-group"


@read_fixtures
def test_read_with_wrong_slug_redirects(Group, logic):
    """/groups/<hashid>/<wrong> should redirect to /groups/<hashid>/<slug>."""
    group = Group.get_by_id.return_value = mock.Mock(slug="my-group")
    matchdict = {"hashid": "1", "slug": "my-gro"}  # Wrong slug.
    request = _mock_request(matchdict=matchdict)
    logic.url_for_group.return_value = "/1/my-group"

    redirect = views.read(request)

    logic.url_for_group.assert_called_once_with(request, group)
    assert redirect.location == "/1/my-group"


@read_fixtures
def test_read_if_not_logged_in_renders_share_group_page(
        Group, renderers):
    """If not logged in should render the "Login to join this group" page."""
    Group.get_by_id.return_value = mock.Mock(slug=mock.sentinel.slug)
    request = _mock_request(authenticated_userid=None, matchdict=_matchdict())

    views.read(request)

    assert renderers.render_to_response.call_args[1]['renderer_name'] == (
        'h:groups/templates/login_to_join.html.jinja2')


@read_fixtures
def test_read_if_not_logged_in_passes_group(Group, renderers):
    """It should pass the group to the template."""
    group = Group.get_by_id.return_value = mock.Mock(slug=mock.sentinel.slug)
    request = _mock_request(authenticated_userid=None, matchdict=_matchdict())

    views.read(request)

    assert renderers.render_to_response.call_args[1]['value']['group'] == (
        group)


@read_fixtures
def test_read_if_not_logged_in_returns_response(
        Group, renderers):
    """It should return the response from render_to_response()."""
    Group.get_by_id.return_value = mock.Mock(slug=mock.sentinel.slug)
    request = _mock_request(authenticated_userid=None, matchdict=_matchdict())
    renderers.render_to_response.return_value = mock.sentinel.response

    response = views.read(request)

    assert response == mock.sentinel.response


@read_fixtures
def test_read_if_not_a_member_encodes_hashid_from_groupid(
        Group, User, hashids):
    """It should encode the hashid from the groupid.

    And use it to get the join URL from route_url().

    """
    request = _mock_request(matchdict=_matchdict())
    group = Group.get_by_id.return_value = mock.Mock(slug=mock.sentinel.slug)
    user = User.get_by_id.return_value = mock.Mock()
    user.groups = []  # The user isn't a member of the group.
    hashids.encode.return_value = mock.sentinel.hashid

    views.read(request)

    assert hashids.encode.call_args[1]['number'] == group.id
    assert request.route_url.call_args[1]['hashid'] == mock.sentinel.hashid


@read_fixtures
def test_read_if_not_a_member_renders_template(
        Group, User, renderers):
    """It should render the "Join this group" template."""
    request = _mock_request(matchdict=_matchdict())
    Group.get_by_id.return_value = mock.Mock(slug=mock.sentinel.slug)
    user = User.get_by_id.return_value = mock.Mock()
    user.groups = []  # The user isn't a member of the group.

    views.read(request)

    assert renderers.render_to_response.call_args[1]['renderer_name'] == (
        'h:groups/templates/join.html.jinja2')


@read_fixtures
def test_read_if_not_a_member_passes_group_to_template(
        Group, User, renderers):
    """It should get the join URL and pass it to the template."""
    request = _mock_request(matchdict=_matchdict())
    group = Group.get_by_id.return_value = mock.Mock(slug=mock.sentinel.slug)
    user = User.get_by_id.return_value = mock.Mock()
    user.groups = []  # The user isn't a member of the group.

    views.read(request)

    assert renderers.render_to_response.call_args[1]['value']['group'] == group


@read_fixtures
def test_read_if_not_a_member_passes_join_url_to_template(
        Group, User, renderers):
    """It should get the join URL and pass it to the template."""
    request = _mock_request(matchdict=_matchdict())
    request.route_url.return_value = mock.sentinel.join_url
    Group.get_by_id.return_value = mock.Mock(slug=mock.sentinel.slug)
    user = User.get_by_id.return_value = mock.Mock()
    user.groups = []  # The user isn't a member of the group.

    views.read(request)

    assert renderers.render_to_response.call_args[1]['value']['join_url'] == (
        mock.sentinel.join_url)


@read_fixtures
def test_read_if_not_a_member_returns_response(Group, User, renderers):
    """It should return the response from render_to_response()."""
    request = _mock_request(matchdict=_matchdict())
    Group.get_by_id.return_value = mock.Mock(slug=mock.sentinel.slug)
    user = User.get_by_id.return_value = mock.Mock()
    user.groups = []  # The user isn't a member of the group.
    renderers.render_to_response.return_value = mock.sentinel.response

    assert views.read(request) == mock.sentinel.response


@read_fixtures
def test_read_if_already_a_member_renders_template(
        Group, User, renderers):
    """It should render the "Share this group" template."""
    request = _mock_request(matchdict=_matchdict())
    group = Group.get_by_id.return_value = mock.Mock(slug=mock.sentinel.slug)
    user = User.get_by_id.return_value = mock.Mock()
    user.groups = [group]  # The user is a member of the group.

    views.read(request)
    assert renderers.render_to_response.call_args[1]['renderer_name'] == (
        'h:groups/templates/read.html.jinja2')


@read_fixtures
def test_read_if_already_a_member_passes_group(Group, User, renderers):
    """It passes the group to the template."""
    request = _mock_request(matchdict=_matchdict())
    group = Group.get_by_id.return_value = mock.Mock(slug=mock.sentinel.slug)
    user = User.get_by_id.return_value = mock.Mock()
    user.groups = [group]  # The user is a member of the group.

    views.read(request)

    assert renderers.render_to_response.call_args[1]['value']['group'] == group


@read_fixtures
def test_read_if_already_a_member_passes_group_url(
        Group, User, logic, renderers):
    """It gets the url from url_for_group() and passes it to the template."""
    request = _mock_request(matchdict=_matchdict())
    group = Group.get_by_id.return_value = mock.Mock(slug=mock.sentinel.slug)
    user = User.get_by_id.return_value = mock.Mock()
    user.groups = [group]  # The user is a member of the group.
    logic.url_for_group.return_value = mock.sentinel.group_url

    views.read(request)

    logic.url_for_group.assert_called_once_with(request, group)
    assert renderers.render_to_response.call_args[1]['value']['group_url'] == (
        mock.sentinel.group_url)


@read_fixtures
def test_read_if_already_a_member_returns_response(
        Group, User, renderers):
    """It should return the response from render_to_response()."""
    request = _mock_request(matchdict=_matchdict())
    group = Group.get_by_id.return_value = mock.Mock(slug=mock.sentinel.slug)
    user = User.get_by_id.return_value = mock.Mock()
    user.groups = [group]  # The user is a member of the group.
    renderers.render_to_response.return_value = mock.sentinel.response

    assert views.read(request) == mock.sentinel.response


# The fixtures required to mock all of join()'s dependencies.
join_fixtures = pytest.mark.usefixtures(
    'User', 'hashids', 'Group', 'logic')


@join_fixtures
def test_join_404s_if_groups_feature_is_off():
    with pytest.raises(httpexceptions.HTTPNotFound):
        views.join(_mock_request(feature=lambda feature: False))


@join_fixtures
def test_join_uses_hashid_from_matchdict_to_get_groupid(hashids):
    matchdict = _matchdict()
    request = _mock_request(matchdict=matchdict)

    views.join(request)

    hashids.decode.assert_called_once_with(
        request, "h.groups", matchdict["hashid"])


@join_fixtures
def test_join_gets_group_by_id(hashids, Group):
    hashids.decode.return_value = "test-group-id"

    views.join(_mock_request(matchdict=_matchdict()))

    Group.get_by_id.assert_called_once_with("test-group-id")


@join_fixtures
def test_join_404s_if_group_not_found(Group):
    Group.get_by_id.return_value = None

    with pytest.raises(httpexceptions.HTTPNotFound):
        views.join(_mock_request(matchdict=_matchdict()))


@join_fixtures
def test_join_gets_user_with_authenticated_userid(User):
    request = _mock_request(matchdict=_matchdict())

    views.join(request)

    User.get_by_id.assert_called_once_with(
        request, request.authenticated_userid)


@join_fixtures
def test_join_adds_user_to_group_members(Group, User):
    Group.get_by_id.return_value = group = mock.Mock()
    User.get_by_id.return_value = mock.sentinel.user

    views.join(_mock_request(matchdict=_matchdict()))

    group.members.append.assert_called_once_with(mock.sentinel.user)


@join_fixtures
def test_join_redirects_to_group_page(Group, logic):
    slug = "test-slug"
    group = Group.get_by_id.return_value = mock.Mock(slug=slug)
    request = _mock_request(matchdict=_matchdict())
    logic.url_for_group.return_value = mock.sentinel.group_url

    redirect = views.join(request)

    logic.url_for_group.assert_called_once_with(request, group)
    assert redirect.status_int == 303
    assert redirect.location == mock.sentinel.group_url


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
def User(request):
    patcher = mock.patch('h.groups.views.accounts_models.User', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def hashids(request):
    patcher = mock.patch('h.groups.views.hashids', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def logic(request):
    patcher = mock.patch('h.groups.views.logic', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def renderers(request):
    patcher = mock.patch('h.groups.views.renderers', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
