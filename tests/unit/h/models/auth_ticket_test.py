from h.models import auth_ticket
from h.models.auth_ticket import AuthTicket


class TestAuthTicket:
    def test_generate_ticket_id(self, mocker):
        urandom = mocker.spy(auth_ticket, "urandom")
        urlsafe_b64encode = mocker.spy(auth_ticket, "urlsafe_b64encode")

        ticket_id = AuthTicket.generate_ticket_id()

        urandom.assert_called_once_with(32)
        urlsafe_b64encode.assert_called_once_with(urandom.spy_return)
        assert ticket_id == urlsafe_b64encode.spy_return.rstrip(b"=").decode("ascii")
