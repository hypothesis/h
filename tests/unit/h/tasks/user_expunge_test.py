import pytest

from h.tasks.user_expunge import expunge_deleted_users


def test_expunge_delete_users(user_expunge_service):
    expunge_deleted_users()

    user_expunge_service.expunge_deleted_users.assert_called_once_with()


@pytest.fixture(autouse=True)
def celery(patch, pyramid_request):
    celery = patch("h.tasks.user_expunge.celery")
    celery.request = pyramid_request
    return celery
