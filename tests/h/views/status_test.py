from unittest import mock

import pytest
from pyramid.httpexceptions import HTTPInternalServerError

from h.views.status import status


@pytest.mark.usefixtures("db")
class TestStatus:
    def test_it_returns_okay_on_success(self, pyramid_request):
        result = status(pyramid_request)
        assert result

    def test_it_fails_when_database_unreachable(self, pyramid_request, db):
        db.execute.side_effect = Exception("explode!")

        with pytest.raises(HTTPInternalServerError) as exc:
            status(pyramid_request)

        assert "Database connection failed" in str(exc.value)

    @pytest.fixture
    def db(self, pyramid_request):
        db = mock.Mock()
        pyramid_request.db = db
        return db
