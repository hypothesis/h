# -*- coding: utf-8 -*-
import pytest
import mock

from h.api import logic


def _mock_annotation(**kwargs):
    """Return a mock h.api.models.Annotation object."""
    annotation = mock.MagicMock()
    annotation.__getitem__.side_effect = kwargs.__getitem__
    annotation.__setitem__.side_effect = kwargs.__setitem__
    annotation.get.side_effect = kwargs.get
    annotation.__contains__.side_effect = kwargs.__contains__
    annotation.update.side_effect = kwargs.update
    annotation.pop.side_effect = kwargs.pop
    return annotation


# The fixtures required to mock all of create_annotation()'s dependencies.
create_annotation_fixtures = pytest.mark.usefixtures(
    'Annotation', 'search_lib')


@create_annotation_fixtures
def test_create_annotation_calls_Annotation(Annotation):
    fields = mock.MagicMock()
    logic.create_annotation(fields)

    Annotation.assert_called_once_with(fields)


@create_annotation_fixtures
def test_create_annotation_calls_prepare(Annotation, search_lib):
    """It should call prepare() once with the annotation."""
    logic.create_annotation({})

    search_lib.prepare.assert_called_once_with(Annotation.return_value)


@create_annotation_fixtures
def test_create_annotation_calls_save(Annotation):
    """It should call save() once."""
    logic.create_annotation({})

    Annotation.return_value.save.assert_called_once_with()


@create_annotation_fixtures
def test_create_annotation_returns_the_annotation(Annotation):
    result = logic.create_annotation({})
    assert result == Annotation.return_value


# The fixtures required to mock all of update_annotation()'s dependencies.
update_annotation_fixtures = pytest.mark.usefixtures('search_lib')


@update_annotation_fixtures
def test_update_annotation_calls_update():
    annotation = _mock_annotation()
    fields = {'foo': 'bar'}

    logic.update_annotation(annotation, fields)

    annotation.update.assert_called_once_with(fields)


@update_annotation_fixtures
def test_update_annotation_calls_prepare(search_lib):
    annotation = _mock_annotation()

    logic.update_annotation(annotation, {})

    search_lib.prepare.assert_called_once_with(annotation)


@update_annotation_fixtures
def test_update_annotation_calls_save():
    annotation = _mock_annotation()

    logic.update_annotation(annotation, {})

    annotation.save.assert_called_once_with()


# The fixtures required to mock all of delete_annotation()'s dependencies.
delete_annotation_fixtures = pytest.mark.usefixtures()


@delete_annotation_fixtures
def test_delete_annotation_calls_delete():
    annotation = mock.MagicMock()

    logic.delete_annotation(annotation)

    annotation.delete.assert_called_once_with()


@pytest.fixture
def Annotation(request):
    patcher = mock.patch('h.api.logic.Annotation', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def search_lib(request):
    patcher = mock.patch('h.api.logic.search_lib', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
