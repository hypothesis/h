# -*- coding: utf-8 -*-
import deform
import mock
import pytest
from pyramid import httpexceptions

from h.groups import views


@mock.patch('h.groups.views.deform.Form')
@mock.patch('h.groups.views.schemas.GroupSchema')
def test_create_group_form_404s_if_groups_feature_is_off(GroupSchema, Form):
    request = mock.Mock(feature=mock.Mock(return_value=False))

    with pytest.raises(httpexceptions.HTTPNotFound):
        views.create_group_form(request)


@mock.patch('h.groups.views.deform.Form')
@mock.patch('h.groups.views.schemas.GroupSchema')
def test_create_group_form_creates_form_with_GroupSchema(GroupSchema, Form):
    test_schema = mock.Mock()
    GroupSchema.return_value = mock.Mock(
        bind=mock.Mock(return_value=test_schema))

    views.create_group_form(request=mock.Mock())

    Form.assert_called_once_with(test_schema)


@mock.patch('h.groups.views.deform.Form')
@mock.patch('h.groups.views.schemas.GroupSchema')
def test_create_group_form_returns_form(GroupSchema, Form):
    test_form = mock.Mock()
    Form.return_value = test_form

    template_data = views.create_group_form(request=mock.Mock())

    assert template_data["form"] == test_form


@mock.patch('h.groups.views.deform.Form')
@mock.patch('h.groups.views.schemas.GroupSchema')
def test_create_group_form_returns_empty_form_data(GroupSchema, Form):
    test_form = mock.Mock()
    Form.return_value = test_form

    template_data = views.create_group_form(request=mock.Mock())

    assert template_data["data"] == {}


@mock.patch('h.groups.views.models.Group')
@mock.patch('h.groups.views.deform.Form')
@mock.patch('h.groups.views.schemas.GroupSchema')
def test_create_group_404s_if_groups_feature_is_off(GroupSchema, Form, Group):
    request = mock.Mock(feature=mock.Mock(return_value=False))

    with pytest.raises(httpexceptions.HTTPNotFound):
        views.create_group(request)


@mock.patch('h.groups.views.models.Group')
@mock.patch('h.groups.views.deform.Form')
@mock.patch('h.groups.views.schemas.GroupSchema')
def test_create_group_inits_form_with_schema(GroupSchema, Form, Group):
    schema = mock.Mock()
    GroupSchema.return_value = mock.Mock(bind=mock.Mock(return_value=schema))

    views.create_group(request=mock.Mock())

    Form.assert_called_once_with(schema)


@mock.patch('h.groups.views.models.Group')
@mock.patch('h.groups.views.deform.Form')
@mock.patch('h.groups.views.schemas.GroupSchema')
def test_create_group_validates_form(GroupSchema, Form, Group):
    Form.return_value = form = mock.Mock()
    form.validate.return_value = {"name": "new group"}
    params = {"foo": "bar"}
    request = mock.Mock(POST=params)

    views.create_group(request)

    form.validate.assert_called_once_with(params.items())


@mock.patch('h.groups.views.models.Group')
@mock.patch('h.groups.views.deform.Form')
@mock.patch('h.groups.views.schemas.GroupSchema')
def test_create_group_rerenders_form_on_validation_failure(
        GroupSchema, Form, Group):
    Form.return_value = form = mock.Mock()
    form.validate.side_effect = deform.ValidationFailure(None, None, None)
    params = {"foo": "bar"}

    template_data = views.create_group(
        request=mock.Mock(params=params, POST=params))

    assert template_data['form'] == form
    assert template_data['data'] == params


@mock.patch('h.groups.views.models.Group')
@mock.patch('h.groups.views.deform.Form')
@mock.patch('h.groups.views.schemas.GroupSchema')
def test_create_group_uses_name_from_validated_data(GroupSchema, Form, Group):
    """It uses the "name" from the validated data to create a new group."""
    Form.return_value = mock.Mock(validate=lambda data: {"name": "test-group"})

    views.create_group(request=mock.Mock())

    Group.assert_called_once_with(name="test-group")


@mock.patch('h.groups.views.models.Group')
@mock.patch('h.groups.views.deform.Form')
@mock.patch('h.groups.views.schemas.GroupSchema')
def test_create_group_adds_group_to_db(GroupSchema, Form, Group):
    """It should add the new group to the database session."""
    group = mock.Mock()
    Group.return_value = group
    request = mock.Mock()

    views.create_group(request)

    request.db.add.assert_called_once_with(group)


@mock.patch('h.groups.views.models.Group')
@mock.patch('h.groups.views.deform.Form')
@mock.patch('h.groups.views.schemas.GroupSchema')
def test_create_group_redirects_to_group_read_page(GroupSchema, Form, Group):
    """After successfully creating a new group it should redirect."""
    group = mock.Mock(id='test-id', slug='test-slug')
    Group.return_value = group
    request = mock.Mock(route_url=mock.Mock(return_value="test-read-url"))

    redirect = views.create_group(request)

    request.route_url.assert_called_once_with(
        "group_read", id="test-id", slug="test-slug")
    assert redirect.status_int == 303
    assert redirect.location == "test-read-url"


@mock.patch('h.groups.views.models.Group')
@mock.patch('h.groups.views.deform.Form')
@mock.patch('h.groups.views.schemas.GroupSchema')
def test_create_group_with_non_ascii_name(GroupSchema, Form, Group):
    name = u"☆ ßüper Gröup ☆"
    request = mock.Mock(params={"name": name})

    views.create_group(request)


@mock.patch('h.groups.views.models.Group')
def test_read_group_404s_if_groups_feature_is_off(Group):
    request = mock.Mock(feature=mock.Mock(return_value=False))

    with pytest.raises(httpexceptions.HTTPNotFound):
        views.read_group(request)


@mock.patch('h.groups.views.models.Group')
def test_read_group_uses_id_from_params(Group):
    request = mock.Mock(matchdict={"id": "1"})

    views.read_group(request)

    Group.get_by_id.assert_called_once_with(1)


@mock.patch('h.groups.views.models.Group')
def test_read_group_returns_the_group(Group):
    request = mock.Mock(matchdict={"id": "1"})
    group = mock.Mock()
    Group.get_by_id.return_value = group

    template_data = views.read_group(request)

    assert template_data["group"] == group


@mock.patch('h.groups.views.models.Group')
def test_read_group_404s_when_group_does_not_exist(Group):
    request = mock.Mock(matchdict={"id": "1"})
    Group.get_by_id.return_value = None

    with pytest.raises(httpexceptions.HTTPNotFound):
        views.read_group(request=request)
