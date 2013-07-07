from unittest import TestCase
from h.models import User

from . import AppTestCase

class UserTest(AppTestCase):

    def test_password_encrypt(self):
        """make sure user passwords are stored encrypted
        """
        u1 = User(username=u'test', password=u'test', email=u'test@example.org')
        self.assertNotEqual(u1.password, 'test')
        self.session.add(u1)
        self.session.flush()
        self.assertNotEqual(u1.password, 'test')



