import re

from h.models import Activation


def test_activation_has_asciinumeric_code(db_session):
    act = Activation()

    db_session.add(act)
    db_session.flush()

    assert re.match(r"[A-Za-z0-9]{12}", act.code)
