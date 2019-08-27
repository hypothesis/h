import click

from h import models


def create_all_dev_data(request):
    """Create all the dev data that doesn't exist yet."""
    factory = DevDataFactory(request)

    factory.upsert_user("user")
    factory.upsert_user("user_2")
    factory.upsert_user("admin", admin=True)
    factory.upsert_user("staff", staff=True)

    request.tm.commit()


class DevDataFactory(object):
    """A class that creates development data if it doesn't already exist."""

    def __init__(self, request):
        self.request = request
        self.db = self.request.db
        self.authority = "hypothes.is"

    def upsert_user(self, username, admin=False, staff=False):

        def existing_user():
            return (
                self.db.query(models.User)
                .filter_by(username=username, authority=self.authority)
                .one_or_none()
            )

        def new_user():
            signup_service = self.request.find_service(name="user_signup")
            user = signup_service.signup(
                username=username,
                authority=self.authority,
                require_activation=False,
            )
            click.echo(f"Created user {user}")
            return user

        user = existing_user() or new_user()
        user.admin = admin
        user.staff = staff
        user.email = f"{username}@example_changed.com"
        user.password = "pass"


@click.command()
@click.pass_context
def devdata(ctx):
    request = ctx.obj["bootstrap"]()
    create_all_dev_data(request)
