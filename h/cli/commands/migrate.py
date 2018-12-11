# -*- coding: utf-8 -*-

import argparse

import click
from alembic.config import CommandLine as _CommandLine
from alembic.config import Config


class CommandLine(_CommandLine):

    """
    A modified version of the default Alembic CommandLine.

    This class suppresses the -c/--config option from the help, and defaults it
    to a specified config file.
    """

    def __init__(self, file_, prog=None):
        self.file_ = file_

        super(CommandLine, self).__init__(prog=prog)

        # This is super sneaky. Grab the config option and suppress its help.
        conf = None
        for a in self.parser._actions:
            if "--config" in a.option_strings:
                conf = a
                break
        if conf:
            conf.help = argparse.SUPPRESS

    def main(self, argv=None):
        options = self.parser.parse_args(argv)
        if not hasattr(options, "cmd"):
            # see http://bugs.python.org/issue9253, argparse
            # behavior changed incompatibly in py3.3
            self.parser.error("too few arguments")
        else:
            cfg = Config(file_=self.file_, ini_section=options.name, cmd_opts=options)
            self.run_cmd(cfg, options)


@click.command(
    add_help_option=False,  # --help is passed through to Alembic
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
@click.pass_context
def migrate(ctx):
    """
    Run Alembic (database migration) commands.

    This command gives preconfigured access to the full Alembic CLI.
    """
    cli = CommandLine(file_="conf/alembic.ini", prog=ctx.command_path)
    cli.main(argv=ctx.args)
