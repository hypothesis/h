import pytest


def test___repr__(factories, helpers):
    job = factories.Job()
    repr_ = repr(job)

    helpers.repr_.assert_called_once_with(
        job,
        [
            "id",
            "name",
            "enqueued_at",
            "scheduled_at",
            "expires_at",
            "priority",
            "tag",
        ],
    )
    assert repr_ == helpers.repr_.return_value


@pytest.fixture(autouse=True)
def helpers(mocker):
    helpers = mocker.patch("h.models.job.helpers")
    # __repr__() needs to return a string or repr() raises.
    helpers.repr_.return_value = "test_string_representation"
    return helpers
