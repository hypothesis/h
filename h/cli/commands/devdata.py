"""
A CLI command for inserting standard dev data into the DB.

Usage:

    bin/hypothesis --dev devdata
"""

import json
import os.path
import pathlib
import shutil
import subprocess
import tempfile

import click

import h
from h import models


class DevDataFactory:
    """Factory class for inserting standard dev data into the DB."""

    def __init__(self, request, devdata_):
        self.db = request.db
        self.tm = request.tm
        self.devdata = devdata_

        self.user_password_service = request.find_service(name="user_password")
        self.group_service = request.find_service(name="group")
        self.group_create_service = request.find_service(name="group_create")

    def create_all(self):
        """
        Create all the standard dev data in the DB.

        Create standard dev data objects (users, groups, etc) if they don't
        exist. If objects with the same identifier already exist in the DB
        (e.g. a user with the same name as a standard dev data user, or a group
        with the same pubid, etc) but those objects have different values for
        some fields, then overwrite those incorrect values with the standard
        values.
        """
        for data_dict in self.devdata:
            type_ = data_dict.pop("type")
            if type_ == "authclient":
                self.upsert_authclient(data_dict)
            elif type_ == "organization":
                self.upsert_organization(data_dict)
            elif type_ == "user":
                self.upsert_user(data_dict)
            elif type_ == "open_group":
                self.upsert_open_group(data_dict)
            elif type_ == "restricted_group":
                self.upsert_restricted_group(data_dict)
            else:
                raise RuntimeError(f"Unrecognized type: {type_}")

        self.tm.commit()

    def upsert_authclient(self, authclient_data):
        authclient = (
            self.db.query(models.AuthClient)
            .filter_by(name=authclient_data["name"])
            .one_or_none()
        )

        if not authclient:
            authclient = models.AuthClient()
            self.db.add(authclient)

        self.setattrs(authclient, authclient_data)

    def upsert_organization(self, organization_data):
        organization = (
            self.db.query(models.Organization)
            .filter_by(pubid=organization_data["pubid"])
            .one_or_none()
        )

        if not organization:
            organization = models.Organization()
            self.db.add(organization)

        self.setattrs(organization, organization_data)

    def upsert_user(self, user_data):
        user = models.User.get_by_username(
            self.db, user_data["username"], user_data["authority"]
        )

        if not user:
            user = models.User()
            self.db.add(user)

        password = user_data.pop("password")
        self.user_password_service.update_password(user, password)

        self.setattrs(user, user_data)

    def upsert_open_group(self, group_data):
        return self.upsert_group(
            group_data, self.group_create_service.create_open_group
        )

    def upsert_restricted_group(self, group_data):
        return self.upsert_group(
            group_data, self.group_create_service.create_restricted_group
        )

    def upsert_group(self, group_data, group_create_method):
        creator = models.User.get_by_username(
            self.db, group_data.pop("creator_username"), group_data["authority"]
        )
        assert creator

        organization = (
            self.db.query(models.Organization)
            .filter_by(pubid=group_data.pop("organization_pubid"))
            .one()
        )

        group = self.group_service.fetch_by_pubid(group_data["pubid"])

        if not group:
            group = group_create_method(group_data.pop("name"), creator.userid, [])

        group.creator = creator
        group.organization = organization
        group.scopes = [
            models.GroupScope(scope=scope) for scope in group_data.pop("scopes")
        ]

        self.setattrs(group, group_data)

    @staticmethod
    def setattrs(object_, attrs):
        for name, value in attrs.items():
            setattr(object_, name, value)


@click.command()
@click.pass_context
def devdata(ctx):
    with tempfile.TemporaryDirectory() as tmpdirname:
        # The directory that we'll clone the devdata git repo into.
        git_dir = os.path.join(tmpdirname, "devdata")

        # Clone the private devdata repo from GitHub.
        # This will fail if Git->GitHub HTTPS authentication isn't set up or if
        # your GitHub account doesn't have access to the private repo.
        subprocess.check_call(
            ["git", "clone", "https://github.com/hypothesis/devdata.git", git_dir]
        )

        # Copy environment variables file into place.
        shutil.copyfile(
            os.path.join(git_dir, "h", "devdata.env"),
            os.path.join(pathlib.Path(h.__file__).parent.parent, ".devdata.env"),
        )

        with open(
            os.path.join(git_dir, "h", "devdata.json"), "r", encoding="utf8"
        ) as handle:
            DevDataFactory(
                ctx.obj["bootstrap"](),
                json.loads(handle.read()),
            ).create_all()
