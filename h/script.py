from clint import args
from clint.textui import colored, puts


usage = """Usage: h [COMMAND]"""
descsription = """\
The Hypothes.is Project Annotation System.
"""


def assets():
    """Build the static assets."""
    cfname = args.pop(0)
    if not cfname:
        puts(colored.red("You must supply a paste configuration."))
        return 2

    from h import bootstrap
    from pyramid_webassets import IWebAssetsEnvironment

    def build(env):
        asset_env = env['registry'].queryUtility(IWebAssetsEnvironment)
        for bundle in asset_env:
            bundle.urls()

    bootstrap(cfname, build)


def run():
    sub_args = args.all
    if not len(args.not_flags):  # Default to dev mode
        sub_args.insert(0, '--reload')
        sub_args.insert(0, 'development.ini')

    from pyramid.scripts.pserve import main
    main(['h'] + sub_args)


def main():
    command = args.pop(0)
    if not command:
        return run()

    try:
        return globals()[command]()
    except KeyError:
        puts(colored.red("Unknown command: '%s'" % command))
        return 2
