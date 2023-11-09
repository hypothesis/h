import pytest
from pyramid.httpexceptions import HTTPSeeOther

from h.views.admin.mailer import mailer_index, mailer_test


class TestMailerIndex:
    def test_when_no_taskid(self, pyramid_request):
        result = mailer_index(pyramid_request)

        assert result == {"taskid": None}

    def test_with_taskid(self, pyramid_request):
        pyramid_request.params["taskid"] = "abcd1234"

        result = mailer_index(pyramid_request)

        assert result == {"taskid": "abcd1234"}


@pytest.mark.usefixtures("mailer", "testmail", "routes")
class TestMailerTest:
    def test_doesnt_mail_when_no_recipient(self, mailer, pyramid_request):
        mailer_test(pyramid_request)

        assert not mailer.send.delay.called

    def test_redirects_when_no_recipient(self, pyramid_request):
        result = mailer_test(pyramid_request)

        assert isinstance(result, HTTPSeeOther)
        assert result.location == "/adm/mailer"

    def test_sends_mail(self, mailer, pyramid_request):
        pyramid_request.params["recipient"] = "meerkat@example.com"

        mailer_test(pyramid_request)

        mailer.send.delay.assert_called_once_with(
            ["meerkat@example.com"], "TEST", "text", "html"
        )

    def test_redirects(self, pyramid_request):
        pyramid_request.params["recipient"] = "meerkat@example.com"

        result = mailer_test(pyramid_request)

        assert isinstance(result, HTTPSeeOther)
        assert result.location == "/adm/mailer?taskid=a1b2c3"


class FakeResult:
    def __init__(self):
        self.task_id = "a1b2c3"


@pytest.fixture
def mailer(patch):
    mailer = patch("h.views.admin.mailer.mailer")
    mailer.send.delay.return_value = FakeResult()
    return mailer


@pytest.fixture
def testmail(patch):
    test = patch("h.views.admin.mailer.test")
    test.generate.side_effect = lambda _, r: ([r], "TEST", "text", "html")
    return test


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("admin.mailer", "/adm/mailer")
