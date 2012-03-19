import apex.forms

from .. models import DBSession

class RegisterForm(apex.forms.RegisterForm):
    def after_signup(self, user):
        print "YEAHHH"
        DBSession.flush()
