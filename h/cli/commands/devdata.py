# -*- coding: utf-8 -*-
from __future__ import print_function

import click

from h import models


def create_all_dev_data(request):
    """Create all the dev data that doesn't exist yet."""
    factory = DevDataFactory(request)

    # Create some Hypothesis users: an admin user, a staff user, a normal user, ...
    factory.user(u"user")
    factory.user(u"admin", admin=True)
    factory.user(u"staff", staff=True)

    # Create the auth client that the Hypothesis client needs to login.
    factory.auth_client(u"a77b3fee-31e8-11e8-b65b-cf64c6731003",
                        name=u"client",
                        grant_type=u"authorization_code",
                        response_type=u"code",
                        redirect_uri=u"http://localhost:5000/app.html")

    # Create auth clients, users etc for the publisher account test site.
    partner_authority = u"partner.org"

    factory.auth_client(u"e2317c70-3cce-11e8-ac47-23c1999ab55a",
                        authority=partner_authority,
                        name=u"publisher_account_test_site_client_credentials",
                        grant_type=u"client_credentials",
                        response_type=None,
                        redirect_uri=None,
                        secret=u"8l1b3f4vkS80k83WEMl47DKfsOraiQk4aHld-gNYOqM")
    factory.auth_client(u"c78ed9e6-3cd1-11e8-b64e-535bf04ec9db",
                        authority=partner_authority,
                        name=u"publisher_account_test_site_client_credentials",
                        grant_type=u"jwt_bearer",
                        response_type=None,
                        redirect_uri=None,
                        secret=u"Zsid_Z1DVD9U-3V9bUN4008QNg9fkjm6jkI0tHIzK6Y")

    publisher_site_admin = factory.user(authority=partner_authority,
                                        username=u"admin")
    publisher_site_organization = factory.organization(u"publisher_account_test",
                                                       partner_authority)

    factory.group(type_="open",
                  name=u"Partner",
                  creator=publisher_site_admin,
                  origins=[u"http://localhost:5050"],
                  organization=publisher_site_organization)

    # Open and restricted groups for the BioPub demo site.
    biopub_admin = factory.user(username=u"biopub_admin")
    biopub_organization = factory.organization(u"BioPub")
    factory.group(type_="open",
                  name=u"BioPub Open",
                  creator=biopub_admin,
                  origins=[u"http://localhost:9000"],
                  organization=biopub_organization)
    factory.group(type_="restricted",
                  name=u"BioPub Restricted",
                  creator=biopub_admin,
                  origins=[u"http://localhost:9000"],
                  organization=biopub_organization)

    request.tm.commit()


class DevDataFactory(object):
    """A class that creates development data if it doesn't already exist."""

    def __init__(self, request):
        self.request = request
        self.db = self.request.db
        # The authority that's used for organizations, groups, users, etc by
        # default when no other authority is explicitly specified.
        self.default_authority = u"hypothes.is"

    def auth_client(self, id_, authority=None, **kwargs):
        """Return the AuthClient with the given ID. Create it if necessary."""
        authority = authority or self.default_authority

        def existing_auth_client():
            """Return the existing AuthClient with the given id_ or None."""
            return self.db.query(models.AuthClient).get(id_)

        def new_auth_client():
            """Create and return a new AuthClient with the given id_."""
            auth_client = models.AuthClient(id=id_, authority=authority, **kwargs)
            self.db.add(auth_client)
            click.echo(u"Created auth client {auth_client}".format(auth_client=auth_client))
            return auth_client

        return existing_auth_client() or new_auth_client()

    def user(self, username, authority=None, admin=False, staff=False):
        """Return the User with the given username and authority. Create it if necessary."""
        authority = authority or self.default_authority

        def existing_user():
            """Return the existing user with the given username and authority, or None."""
            return self.db.query(models.User).filter_by(username=username, authority=authority).one_or_none()

        def new_user():
            """Create and return a new user with the given username and authority."""
            signup_service = self.request.find_service(name=u"user_signup")
            user = signup_service.signup(
                username=username,
                authority=authority,
                admin=admin,
                staff=staff,
                email=u"{username}@example.com".format(username=username),
                password=u"pass",
                require_activation=False,
            )
            click.echo(u"Created user {user}".format(user=user))
            return user

        return existing_user() or new_user()

    def organization(self, name, authority=None, logo=None):
        """Return an organization with the given name and authority. Create it if necessary."""
        authority = authority or self.default_authority

        def existing_organization():
            """Return the first existing organization with the given name and authority, or None."""
            existing_organizations = self.db.query(models.Organization).filter_by(name=name, authority=authority).all()
            if existing_organizations:
                return existing_organizations[0]
            return None

        def new_organization():
            """Create and return a new organization with the given name and authority."""
            organization_service = self.request.find_service(name=u"organization")
            organization = organization_service.create(name, authority, logo)
            click.echo(u"Created organization {organization}".format(organization=organization))
            return organization

        return existing_organization() or new_organization()

    def group(self, type_, name, creator, organization, **kwargs):
        """Return a group with the given name, creator and organization. Create it if necessary."""
        def existing_group():
            """Return an existing group with the given name, creator and organization, or None."""
            existing_groups = self.db.query(models.Group).filter_by(name=name, creator=creator, organization=organization).all()
            if existing_groups:
                return existing_groups[0]
            return None

        def new_group():
            """Create and return a group with the given name, creator and organization."""
            group = create_method(name=name, userid=creator.userid, organization=organization, **kwargs)
            click.echo(u"Created group {group}".format(group=group))
            return group

        group_service = self.request.find_service(name=u"group")

        if type_ == u"open":
            create_method = group_service.create_open_group
        elif type_ == u"restricted":
            create_method = group_service.create_restricted_group
        else:
            raise ValueError('type_ must be either "open" or "restricted"')

        return existing_group() or new_group()


@click.command()
@click.pass_context
def devdata(ctx):
    if not ctx.obj["dev"]:
        raise click.ClickException("Dev data should only be created in dev mode (--dev)")
    request = ctx.obj["bootstrap"]()
    create_all_dev_data(request)
