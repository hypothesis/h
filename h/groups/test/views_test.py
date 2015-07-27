# -*- coding: utf-8 -*-
import deform
import mock
import pytest
from pyramid import httpexceptions

from h.groups import views


def _mock_request(feature=None, settings=None, params=None,
                  authenticated_userid=None, route_url=None, **kwargs):
    """Return a mock Pyramid request object."""
    params = params or {"foo": "bar"}
    return mock.Mock(
        feature=feature or (lambda feature: True),
        registry=mock.Mock(settings=settings or {
            "h.hashids.salt": "test salt"}),
        params=params, POST=params,
        authenticated_userid=authenticated_userid or "acct:fred@hypothes.is",
        route_url=route_url or mock.Mock(return_value="test-read-url"),
        **kwargs)

# The fixtures required to mock all of create_group_form()'s dependencies.
create_group_form_fixtures = pytest.mark.usefixtures('GroupSchema', 'Form')


@create_group_form_fixtures
def test_create_group_form_404s_if_groups_feature_is_off():
    with pytest.raises(httpexceptions.HTTPNotFound):
        views.create_group_form(_mock_request(feature=lambda feature: False))


@create_group_form_fixtures
def test_create_group_form_creates_form_with_GroupSchema(GroupSchema, Form):
    test_schema = mock.Mock()
    GroupSchema.return_value = mock.Mock(
        bind=mock.Mock(return_value=test_schema))

    views.create_group_form(request=_mock_request())

    Form.assert_called_once_with(test_schema)


@create_group_form_fixtures
def test_create_group_form_returns_form(Form):
    test_form = mock.Mock()
    Form.return_value = test_form

    template_data = views.create_group_form(request=_mock_request())

    assert template_data["form"] == test_form


@create_group_form_fixtures
def test_create_group_form_returns_empty_form_data(Form):
    test_form = mock.Mock()
    Form.return_value = test_form

    template_data = views.create_group_form(request=_mock_request())

    assert template_data["data"] == {}


# The fixtures required to mock all of create_group()'s dependencies.
create_group_fixtures = pytest.mark.usefixtures(
    'GroupSchema', 'Form', 'Group', 'User', 'hashids')


@create_group_fixtures
def test_create_group_404s_if_groups_feature_is_off():
    with pytest.raises(httpexceptions.HTTPNotFound):
        views.create_group(_mock_request(feature=lambda feature: False))


@create_group_fixtures
def test_create_group_inits_form_with_schema(GroupSchema, Form):
    schema = mock.Mock()
    GroupSchema.return_value = mock.Mock(bind=mock.Mock(return_value=schema))

    views.create_group(request=_mock_request())

    Form.assert_called_once_with(schema)


@create_group_fixtures
def test_create_group_validates_form(Form):
    Form.return_value = form = mock.Mock()
    form.validate.return_value = {"name": "new group"}
    request = _mock_request()

    views.create_group(request)

    form.validate.assert_called_once_with(request.params.items())


@create_group_fixtures
def test_create_group_rerenders_form_on_validation_failure(Form):
    Form.return_value = form = mock.Mock()
    form.validate.side_effect = deform.ValidationFailure(None, None, None)
    params = {"foo": "bar"}

    template_data = views.create_group(_mock_request())

    assert template_data['form'] == form
    assert template_data['data'] == params


@create_group_fixtures
def test_create_group_gets_user_with_authenticated_id(Form, User):
    """It uses the "name" from the validated data to create a new group."""
    Form.return_value = mock.Mock(validate=lambda data: {"name": "test-group"})
    request = _mock_request()

    views.create_group(request)

    User.get_by_id.assert_called_once_with(
        request, request.authenticated_userid)


@create_group_fixtures
def test_create_group_uses_name_from_validated_data(Form, User, Group):
    """It uses the "name" from the validated data to create a new group."""
    Form.return_value = mock.Mock(validate=lambda data: {"name": "test-group"})
    User.get_by_id.return_value = user = mock.Mock()

    views.create_group(_mock_request())

    Group.assert_called_once_with(name="test-group", creator=user)


@create_group_fixtures
def test_create_group_adds_group_to_db(Group):
    """It should add the new group to the database session."""
    group = mock.Mock(id=6)
    Group.return_value = group
    request = _mock_request()

    views.create_group(request)

    request.db.add.assert_called_once_with(group)


@create_group_fixtures
def test_create_group_redirects_to_group_read_page(Group, hashids):
    """After successfully creating a new group it should redirect."""
    group = mock.Mock(id='test-id', slug='test-slug')
    Group.return_value = group
    request = _mock_request()
    hashids.encode.return_value = "testhashid"

    redirect = views.create_group(request)

    request.route_url.assert_called_once_with(
        "group_read", hashid="testhashid", slug="test-slug")
    assert redirect.status_int == 303
    assert redirect.location == "test-read-url"


@create_group_fixtures
def test_create_group_with_non_ascii_name():
    views.create_group(_mock_request(params={"name": u"☆ ßüper Gröup ☆"}))


# The fixtures required to mock all of read_group()'s dependencies.
read_group_fixtures = pytest.mark.usefixtures('Group', 'hashids')


@read_group_fixtures
def test_read_group_404s_if_groups_feature_is_off():
    with pytest.raises(httpexceptions.HTTPNotFound):
        views.read_group(_mock_request(feature=lambda feature: False))


@read_group_fixtures
def test_read_group_decodes_hashid(hashids):
    request = _mock_request(matchdict={"hashid": "1", "slug": "slug"})

    views.read_group(request)

    hashids.decode.assert_called_once_with(
        request, "h.groups", "1")


@read_group_fixtures
def test_read_group_gets_group_by_id(Group, hashids):
    hashids.decode.return_value = 1

    views.read_group(_mock_request(matchdict={"hashid": "1", "slug": "slug"}))

    Group.get_by_id.assert_called_once_with(1)


@read_group_fixtures
def test_read_group_returns_the_group(Group, hashids):
    group = mock.Mock(slug="slug")
    Group.get_by_id.return_value = group
    hashids.decode.return_value = 1

    template_data = views.read_group(_mock_request(
        matchdict={"hashid": "1", "slug": "slug"}))

    assert template_data["group"] == group


@read_group_fixtures
def test_read_group_404s_when_group_does_not_exist(Group, hashids):
    Group.get_by_id.return_value = None
    hashids.decode.return_value = 1

    with pytest.raises(httpexceptions.HTTPNotFound):
        views.read_group(_mock_request(
            matchdict={"hashid": "1", "slug": "slug"}))


@read_group_fixtures
def test_read_group_without_slug_redirects(Group):
    """/groups/<hashid> should redirect to /groups/<hashid>/<slug>."""
    Group.return_value = mock.Mock(slug="my-group")
    matchdict = {"hashid": "1"}  # No slug.
    request = _mock_request(
        matchdict=matchdict,
        route_url=mock.Mock(return_value="/1/my-group"))

    redirect = views.read_group(request)

    assert request.route_url.called_with(
        "group_read", hashid="1", slug="my-group")
    assert redirect.location == "/1/my-group"


@read_group_fixtures
def test_read_group_with_wrong_slug_redirects(Group):
    """/groups/<hashid>/<wrong> should redirect to /groups/<hashid>/<slug>."""
    Group.return_value = mock.Mock(slug="my-group")
    matchdict = {"hashid": "1", "slug": "my-gro"}
    request = _mock_request(
        matchdict=matchdict,
        route_url=mock.Mock(return_value="/1/my-group"))

    redirect = views.read_group(request)

    assert request.route_url.called_with(
        "group_read", hashid="1", slug="my-group")
    assert redirect.location == "/1/my-group"


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
