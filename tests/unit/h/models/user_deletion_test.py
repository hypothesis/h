import pytest


def test___repr__(factories, helpers):
    user_deletion = factories.UserDeletion()
    repr_ = repr(user_deletion)

    helpers.repr_.assert_called_once_with(
        user_deletion,
        [
            "id",
            "userid",
            "requested_at",
            "requested_by",
            "tag",
            "registered_date",
            "num_annotations",
        ],
    )
    assert repr_ == helpers.repr_.return_value


@pytest.fixture(autouse=True)
def helpers(mocker):
    helpers = mocker.patch("h.models.user_deletion.helpers")
    # __repr__() needs to return a string or repr() raises.
    helpers.repr_.return_value = "test_string_representation"
    return helpers
