import click

from h import models
from h.models.auth_client import GrantType
from h.security import token_urlsafe


@click.group()
def authclient():
    """Manage OAuth clients."""


@authclient.command()
@click.option("--name", prompt=True, help="The name of the client")
@click.option(
    "--authority",
    prompt=True,
    help="The authority (domain name) of the resources managed by the client",
)
@click.option(
    "--type",
    "type_",
    type=click.Choice(["public", "confidential"]),
    prompt=True,
    help="The OAuth client type (public, or confidential)",
)
@click.option(
    "--redirect-uri",
    prompt=False,
    help="URI for browser redirect after authorization. Required if grant type is 'authorization_code'",
)
@click.option(
    "--grant-type",
    type=click.Choice(GrantType.__members__),
    prompt=False,
    help="An allowable grant type",
)
@click.pass_context
def add(
    ctx, name, authority, type_, redirect_uri, grant_type
):  # pylint:disable=too-many-arguments
    """Create a new OAuth client."""
    request = ctx.obj["bootstrap"]()

    client = models.AuthClient(name=name, authority=authority)
    if type_ == "confidential":
        client.secret = token_urlsafe()
    client.redirect_uri = redirect_uri
    client.grant_type = grant_type
    request.db.add(client)
    request.db.flush()

    id_ = client.id
    secret = client.secret

    request.tm.commit()

    message = f"OAuth client for {authority} created\nClient ID: {id_}"
    if type_ == "confidential":
        message += f"\nClient Secret: {secret}"

    click.echo(message)
