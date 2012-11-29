import clik

from h import __version__


version = __version__
description = """\
The Hypothes.is Project Annotation System
"""


command = clik.App(
    'hypothesis',
    version=version,
    description=description,
)


@command(usage='CONFIG_FILE')
def assets(args, console):
    """Build the static assets."""

    if len(args) == 0:
        console.error('You must supply a paste configuration file.')
        return 2

    from h import bootstrap
    from pyramid_webassets import IWebAssetsEnvironment

    def build(env):
        asset_env = env['registry'].queryUtility(IWebAssetsEnvironment)
        for bundle in asset_env:
            bundle.urls()

    bootstrap(args[0], build)


@command
def run(args):
    """Run the server.

    With no arguments, starts the server in development mode using the
    configuration found in `deveopment.ini` and a hot code reloader enabled.
    """
    if not len(args):  # Default to dev mode
        args.append('development.ini')
        args.append('--reload')

    from pyramid.scripts.pserve import main
    main(['h'] + args)


main = command.main
