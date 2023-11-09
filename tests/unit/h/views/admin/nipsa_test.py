import pytest
from pyramid import httpexceptions

from h.views.admin.nipsa import UserNotFoundError, nipsa_add, nipsa_index, nipsa_remove


@pytest.mark.usefixtures("nipsa_service", "routes", "users")
class TestNipsaIndex:
    def test_lists_flagged_usernames(self, pyramid_request):
        result = nipsa_index(pyramid_request)

        assert set(result["userids"]) == {
            "acct:kiki@example.com",
            "acct:ursula@foo.org",
            "acct:osono@example.com",
        }

    def test_lists_flagged_usernames_no_results(self, nipsa_service, pyramid_request):
        nipsa_service.flagged = set([])

        result = nipsa_index(pyramid_request)

        assert result["userids"] == []


@pytest.mark.usefixtures("nipsa_service", "routes", "users")
class TestNipsaAddRemove:
    def test_add_flags_user(self, nipsa_service, pyramid_request, users):
        pyramid_request.params = {"add": "carl", "authority": "foo.org"}

        nipsa_add(pyramid_request)

        assert users["carl"] in nipsa_service.flagged

    @pytest.mark.parametrize("user", ["", "donkeys"])
    def test_add_raises_when_user_not_found(self, user, pyramid_request):
        pyramid_request.params = {"add": user, "authority": "example.com"}

        with pytest.raises(UserNotFoundError):
            nipsa_add(pyramid_request)

    def test_add_redirects_to_index(self, pyramid_request):
        pyramid_request.params = {"add": "carl", "authority": "foo.org"}

        result = nipsa_add(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == "/adm/nipsa"

    def test_remove_unflags_user(self, nipsa_service, pyramid_request, users):
        pyramid_request.params = {"remove": "acct:kiki@example.com"}

        nipsa_remove(pyramid_request)

        assert users["kiki"] not in nipsa_service.flagged

    @pytest.mark.parametrize("user", ["", "donkeys", "\x00"])
    def test_remove_raises_when_user_not_found(self, user, pyramid_request):
        pyramid_request.params = {"remove": user}

        with pytest.raises(UserNotFoundError):
            nipsa_remove(pyramid_request)

    def test_form_request_user_strips_spaces(
        self, nipsa_service, pyramid_request, users
    ):
        pyramid_request.params = {"add": "    carl   ", "authority": "   foo.org     "}

        nipsa_add(pyramid_request)

        assert users["carl"] in nipsa_service.flagged

    def test_remove_redirects_to_index(self, pyramid_request):
        pyramid_request.params = {"remove": "acct:ursula@foo.org"}

        result = nipsa_remove(pyramid_request)

        assert isinstance(result, httpexceptions.HTTPSeeOther)
        assert result.location == "/adm/nipsa"


class FakeNipsaService:
    def __init__(self, users):
        self.flagged = {u for u in users if u.nipsa}

    def fetch_all_flagged_userids(self):
        return {u.userid for u in self.flagged}

    def flag(self, user):
        self.flagged.add(user)

    def unflag(self, user):
        self.flagged.remove(user)


@pytest.fixture
def nipsa_service(pyramid_config, users):
    service = FakeNipsaService(list(users.values()))
    pyramid_config.register_service(service, name="nipsa")
    return service


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("admin.nipsa", "/adm/nipsa")


@pytest.fixture
def users(db_session, factories):
    users = {
        "carl": factories.User(username="carl", authority="foo.org"),
        "kiki": factories.User(username="kiki", authority="example.com", nipsa=True),
        "ursula": factories.User(username="ursula", authority="foo.org", nipsa=True),
        "osono": factories.User(username="osono", authority="example.com", nipsa=True),
    }
    db_session.flush()
    return users
