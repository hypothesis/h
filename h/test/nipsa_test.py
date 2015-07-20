import mock
from pyramid import testing
from pyramid import httpexceptions

from h import nipsa


@mock.patch("h.nipsa.nipsa_api")
def test_index_with_no_nipsad_users(nipsa_api):
    nipsa_api.index.return_value = []

    assert nipsa.index(testing.DummyRequest()) == {"userids": []}


@mock.patch("h.nipsa.nipsa_api")
def test_index_with_one_nipsad_users(nipsa_api):
    nipsa_api.index.return_value = ["acct:kiki@hypothes.is"]

    assert nipsa.index(testing.DummyRequest()) == {"userids": ["kiki"]}


@mock.patch("h.nipsa.nipsa_api")
def test_index_with_multiple_nipsad_users(nipsa_api):
    nipsa_api.index.return_value = [
        "acct:kiki@hypothes.is", "acct:ursula@hypothes.is",
        "acct:osono@hypothes.is"]

    assert nipsa.index(testing.DummyRequest()) == {
        "userids": ["kiki", "ursula", "osono"]}


@mock.patch("h.nipsa.nipsa_api")
def test_nipsa_calls_nipsa_api_with_userid(nipsa_api):
    request = testing.DummyRequest(params={"add": "kiki"})

    nipsa.nipsa(request)

    nipsa_api.nipsa.assert_called_once_with(request, "acct:kiki@example.com")


@mock.patch("h.nipsa.index")
@mock.patch("h.nipsa.nipsa_api")
def test_nipsa_returns_index(nipsa_api, index):
    request = testing.DummyRequest(params={"add": "kiki"})
    index.return_value = "Keine Bange!"

    assert nipsa.nipsa(request) == "Keine Bange!"


@mock.patch("h.nipsa.nipsa_api")
def test_unnipsa_calls_nipsa_api_with_userid(nipsa_api):
    request = mock.Mock(params={"remove": "kiki"}, domain="hypothes.is")

    nipsa.unnipsa(request)

    nipsa_api.unnipsa.assert_called_once_with(request, "acct:kiki@hypothes.is")


@mock.patch("h.nipsa.nipsa_api")
def test_unnipsa_redirects_to_index(nipsa_api):
    request = mock.Mock(
        params={"remove": "kiki"}, domain="hypothes.is",
        route_url=mock.Mock(return_value="/nipsa"))

    response = nipsa.unnipsa(request)

    assert isinstance(response, httpexceptions.HTTPSeeOther)
    assert response.location == "/nipsa"
