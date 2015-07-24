# -*- coding: utf-8 -*-
import deform
import mock
import pytest
from pyramid import httpexceptions

from h.groups import views


# The fixtures required to mock all of create_group_form()'s dependencies.
create_group_form_fixtures = pytest.mark.usefixtures('GroupSchema', 'Form')


@create_group_form_fixtures
def test_create_group_form_404s_if_groups_feature_is_off():
    request = mock.Mock(feature=mock.Mock(return_value=False))

    with pytest.raises(httpexceptions.HTTPNotFound):
        views.create_group_form(request)


@create_group_form_fixtures
def test_create_group_form_creates_form_with_GroupSchema(GroupSchema, Form):
    test_schema = mock.Mock()
    GroupSchema.return_value = mock.Mock(
        bind=mock.Mock(return_value=test_schema))

    views.create_group_form(request=mock.Mock())

    Form.assert_called_once_with(test_schema)


@create_group_form_fixtures
def test_create_group_form_returns_form(Form):
    test_form = mock.Mock()
    Form.return_value = test_form

    template_data = views.create_group_form(request=mock.Mock())

    assert template_data["form"] == test_form


@create_group_form_fixtures
def test_create_group_form_returns_empty_form_data(Form):
    test_form = mock.Mock()
    Form.return_value = test_form

    template_data = views.create_group_form(request=mock.Mock())

    assert template_data["data"] == {}


# The fixtures required to mock all of create_group()'s dependencies.
create_group_fixtures = pytest.mark.usefixtures(
    'GroupSchema', 'Form', 'Group', 'User', '_encode_hashid')


@create_group_fixtures
def test_create_group_404s_if_groups_feature_is_off():
    request = mock.Mock(feature=mock.Mock(return_value=False))

    with pytest.raises(httpexceptions.HTTPNotFound):
        views.create_group(request)


@create_group_fixtures
def test_create_group_inits_form_with_schema(GroupSchema, Form):
    schema = mock.Mock()
    GroupSchema.return_value = mock.Mock(bind=mock.Mock(return_value=schema))
    request = mock.Mock(registry=mock.Mock(settings={"secret_key": "secret"}))

    views.create_group(request=request)

    Form.assert_called_once_with(schema)


@create_group_fixtures
def test_create_group_validates_form(Form):
    Form.return_value = form = mock.Mock()
    form.validate.return_value = {"name": "new group"}
    params = {"foo": "bar"}
    request = mock.Mock(
        POST=params,
        registry=mock.Mock(settings={"secret_key": "secret"}))

    views.create_group(request)

    form.validate.assert_called_once_with(params.items())


@create_group_fixtures
def test_create_group_rerenders_form_on_validation_failure(Form):
    Form.return_value = form = mock.Mock()
    form.validate.side_effect = deform.ValidationFailure(None, None, None)
    params = {"foo": "bar"}

    template_data = views.create_group(
        request=mock.Mock(params=params, POST=params))

    assert template_data['form'] == form
    assert template_data['data'] == params


@create_group_fixtures
def test_create_group_gets_user_with_authenticated_id(Form, User):
    """It uses the "name" from the validated data to create a new group."""
    Form.return_value = mock.Mock(validate=lambda data: {"name": "test-group"})
    request = mock.Mock(
        registry=mock.Mock(settings={"secret_key": "secret"}),
        authenticated_userid="acct:fred@hypothes.is")

    views.create_group(request)

    User.get_by_id.assert_called_once_with(request, "acct:fred@hypothes.is")


@create_group_fixtures
def test_create_group_uses_name_from_validated_data(Form, User, Group):
    """It uses the "name" from the validated data to create a new group."""
    Form.return_value = mock.Mock(validate=lambda data: {"name": "test-group"})
    User.get_by_id.return_value = user = mock.Mock()
    request = mock.Mock(registry=mock.Mock(settings={"secret_key": "secret"}))

    views.create_group(request)

    Group.assert_called_once_with(name="test-group", creator=user)


@create_group_fixtures
def test_create_group_adds_group_to_db(Group):
    """It should add the new group to the database session."""
    group = mock.Mock(id=6)
    Group.return_value = group
    request = mock.Mock(registry=mock.Mock(settings={"secret_key": "secret"}))

    views.create_group(request)

    request.db.add.assert_called_once_with(group)


@create_group_fixtures
def test_create_group_redirects_to_group_read_page(Group, _encode_hashid):
    """After successfully creating a new group it should redirect."""
    group = mock.Mock(id='test-id', slug='test-slug')
    Group.return_value = group
    request = mock.Mock(
        registry=mock.Mock(settings={"secret_key": "secret"}),
        route_url=mock.Mock(return_value="test-read-url"))
    _encode_hashid.return_value = "testhashid"

    redirect = views.create_group(request)

    request.route_url.assert_called_once_with(
        "group_read", hashid="testhashid", slug="test-slug")
    assert redirect.status_int == 303
    assert redirect.location == "test-read-url"


@create_group_fixtures
def test_create_group_with_non_ascii_name():
    name = u"☆ ßüper Gröup ☆"
    request = mock.Mock(
        params={"name": name},
        registry=mock.Mock(settings={"secret_key": "secret"}))

    views.create_group(request)


# The fixtures required to mock all of read_group()'s dependencies.
read_group_fixtures = pytest.mark.usefixtures('Group', '_decode_hashid')


@read_group_fixtures
def test_read_group_404s_if_groups_feature_is_off():
    request = mock.Mock(feature=mock.Mock(return_value=False))

    with pytest.raises(httpexceptions.HTTPNotFound):
        views.read_group(request)


@read_group_fixtures
def test_read_group_decodes_hashid(_decode_hashid):
    request = mock.Mock(
        matchdict={"hashid": "1"},
        registry=mock.Mock(settings={"secret_key": "secret"}))

    views.read_group(request)

    _decode_hashid.assert_called_once_with(request, "1")


@read_group_fixtures
def test_read_group_gets_group_by_id(Group, _decode_hashid):
    request = mock.Mock(
        matchdict={"hashid": "1"},
        registry=mock.Mock(settings={"secret_key": "secret"}))
    _decode_hashid.return_value = 1

    views.read_group(request)

    Group.get_by_id.assert_called_once_with(1)


@read_group_fixtures
def test_read_group_returns_the_group(Group, _decode_hashid):
    request = mock.Mock(
        matchdict={"hashid": "1"},
        registry=mock.Mock(settings={"secret_key": "secret"}))
    group = mock.Mock()
    Group.get_by_id.return_value = group
    _decode_hashid.return_value = 1

    template_data = views.read_group(request)

    assert template_data["group"] == group


@read_group_fixtures
def test_read_group_404s_when_group_does_not_exist(Group, _decode_hashid):
    request = mock.Mock(
        matchdict={"hashid": "1"},
        registry=mock.Mock(settings={"secret_key": "secret"}))
    Group.get_by_id.return_value = None
    _decode_hashid.return_value = 1

    with pytest.raises(httpexceptions.HTTPNotFound):
        views.read_group(request=request)


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
def _encode_hashid(request):
    patcher = mock.patch('h.groups.views._encode_hashid', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def _decode_hashid(request):
    patcher = mock.patch('h.groups.views._decode_hashid', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
