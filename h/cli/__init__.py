import functools
import logging

import click
from pyramid import paster, path
from pyramid.request import Request

from h import __version__

log = logging.getLogger("h")

SUBCOMMANDS = (
    "h.cli.commands.annotation_id.annotation_id",
    "h.cli.commands.authclient.authclient",
    "h.cli.commands.celery.celery",
    "h.cli.commands.devdata.devdata",
    "h.cli.commands.move_uri.move_uri",
    "h.cli.commands.normalize_uris.normalize_uris",
    "h.cli.commands.search.search",
    "h.cli.commands.user.user",
    "h.cli.commands.create_annotations.create_annotations",
)


def bootstrap(app_url, dev=False):  # noqa: FBT002
    """
    Bootstrap the application from the given arguments.

    Returns a bootstrapped request object.
    """
    # In development, we will happily provide a default APP_URL, but it must be
    # set in production mode.
    if not app_url:
        if dev:
            app_url = "http://localhost:5000"
        else:
            raise click.ClickException("the app URL must be set in production mode!")  # noqa: EM101, TRY003

    config = "conf/development.ini" if dev else "conf/production.ini"

    paster.setup_logging(config)
    request = Request.blank("/", base_url=app_url)
    env = paster.bootstrap(config, request=request)
    request.root = env["root"]
    return request


@click.group()
@click.option(
    "--app-url",
    help="The base URL for the application",
    envvar="APP_URL",
    metavar="URL",
)
@click.option(
    "--dev", help="Use defaults suitable for development?", default=False, is_flag=True
)
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx, app_url, dev):
    ctx.obj["bootstrap"] = functools.partial(bootstrap, app_url, dev)


def main():
    resolver = path.DottedNameResolver()
    for cmd in SUBCOMMANDS:
        cli.add_command(resolver.resolve(cmd))
    cli(prog_name="hypothesis", obj={})


if __name__ == "__main__":
    main()
