# -*- coding: utf-8 -*-
"""Command to run an interactive shell with application context."""

import click

BANNER = """Environment:
  m, models    The `h.models` module.
  registry     Active Pyramid registry.
  request      Active request object.
  session      Active database session.
"""


def autodetect():
    try:
        import bpython  # noqa

        return "bpython"
    except ImportError:
        try:
            import IPython  # noqa

            return "ipython"
        except ImportError:
            pass

    return "plain"


def bpython(**locals_):
    import bpython

    bpython.embed(locals_, banner=BANNER)


def ipython(**locals_):
    from IPython import start_ipython
    from traitlets.config import get_config

    c = get_config()
    c.TerminalInteractiveShell.banner2 = BANNER
    start_ipython(argv=[], config=c, user_ns=locals_)


def plain(**locals_):
    import code

    code.interact(banner=BANNER, local=locals_)


@click.command("shell")
@click.option(
    "--type",
    "type_",
    type=click.Choice(["bpython", "ipython", "plain"]),
    help="What type of shell to use, default will autodetect.",
)
@click.pass_obj
def shell(config, type_):
    """Open a shell with the h application environment preconfigured."""
    if type_ is None:
        type_ = autodetect()

    runner = {"bpython": bpython, "ipython": ipython, "plain": plain}[type_]

    from h import models

    request = config["bootstrap"]()
    locals_ = {
        "m": models,
        "models": models,
        "registry": request.registry,
        "request": request,
        "session": request.db,
    }

    try:
        runner(**locals_)
    except ImportError:
        raise click.ClickException("The {!r} shell is not available.".format(type_))
