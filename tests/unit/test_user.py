from unittest import TestCase
from h.models import User

from . import AppTestCase

class UserTest(AppTestCase):

    def test_password_encrypt(self):
        """make sure user passwords are stored encrypted
        """
        u1 = User(username=u'test', password=u'test', email=u'test@example.org')
        assert u1.password != 'test'
        self.db.add(u1)
        self.db.flush()
        assert u1.password != 'test'



